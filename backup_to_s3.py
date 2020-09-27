"""Script to run image capture screenshots for state data pages.
"""

from datetime import datetime
import io
import json
import os
from pytz import timezone
import sys
import time

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import boto3
from loguru import logger
import pandas as pd
import requests
import yaml

parser = ArgumentParser(
    description=__doc__,
    formatter_class=RawDescriptionHelpFormatter)

parser.add_argument(
    '--temp-dir',
    default='/tmp/public-cache',
    help='Local temp dir for snapshots')

parser.add_argument('--states',
    default='',
    help='Comma-separated list of state 2-letter names. If present, will only screenshot those.')

parser.add_argument('--phantomjscloud-key', default='',
    help='API key for PhantomJScloud, used for browser image capture')

# Args relating to S3 setup

parser.add_argument(
    '--s3-bucket',
    default='covid-data-archive',
    help='S3 bucket name')

parser.add_argument(
    '--s3-subfolder',
    default='state_screenshots',
    help='Name of subfolder on S3 bucket to upload files to')

parser.add_argument('--push-to-s3', dest='push_to_s3', action='store_true', default=False,
    help='Push screenshots to S3')

# Determines which screenshots we're aiming to take; these may have different schedules. Only one
# can be true at a time

group = parser.add_mutually_exclusive_group(required=True)

group.add_argument('--screenshot-core-urls', dest='core_urls', action='store_true', default=False,
    help='Screenshot core data URLs from States Info')

group.add_argument('--screenshot-crdt-urls', dest='crdt_urls', action='store_true', default=False,
    help='Screenshot CRDT data URLs')

group.add_argument('--screenshot-ltc-urls', dest='ltc_urls', action='store_true', default=False,
    help='Screenshot LTC data URLs')


class S3Backup():

    def __init__(self, bucket_name, s3_subfolder):
        self.s3 = boto3.resource('s3')
        self.bucket_name = bucket_name
        self.bucket = self.s3.Bucket(self.bucket_name)
        self.s3_subfolder = s3_subfolder

    def get_s3_path(self, local_path, state):
        # CDC goes into its own top-level folder to not mess with state_screenshots
        if state == 'CDC':
            return os.path.join(state, os.path.basename(local_path))
        
        return os.path.join(self.s3_subfolder, state, os.path.basename(local_path))

    # uploads file from local path with specified name
    def upload_file(self, local_path, state):
        extra_args = {}
        if local_path.endswith('.png'):
            extra_args = {'ContentType': 'image/png'}
        elif local_path.endswith('.pdf'):
            extra_args = {'ContentType': 'application/pdf', 'ContentDisposition': 'inline'}
        elif local_path.endswith('.xlsx') or local_path.endswith('.xls'):
            extra_args = {'ContentType': 'application/vnd.ms-excel', 'ContentDisposition': 'inline'}

        s3_path = self.get_s3_path(local_path, state)
        logger.info(f'Uploading file at {local_path} to {s3_path}')
        self.s3.meta.client.upload_file(local_path, self.bucket_name, s3_path, ExtraArgs=extra_args)


class Screenshotter():

    def __init__(self, local_dir, s3_backup, phantomjscloud_key, config):
        self.phantomjs_url = 'https://phantomjscloud.com/api/browser/v2/%s/' % phantomjscloud_key
        self.local_dir = local_dir
        self.s3_backup = s3_backup
        self.config = config


    def get_state_config(self, state, suffix):
        if suffix == 'secondary' and self.config['secondary']:
            # grab any special-casing if it exists
            return self.config['secondary'].get(state)
        if suffix == 'tertiary' and self.config['tertiary']:
            return self.config['tertiary'].get(state)
        if suffix == '':
            return self.config['primary'].get(state)
        return None


    # makes a PhantomJSCloud call to data_url and saves the output to specified path
    def save_url_image_to_path(self, state, data_url, path, state_config=None):
        """Saves URL image from data_url to the specified path.

        Parameters
        ----------
        state : str
            Two-letter abbreviation of the state or territory. Used for special-casing sizes, etc.

        data_url : str
            URL of data site to save

        path : str
            Local path to which to save .png screenshot of data_url

        state_config : dict
            If exists, this is a dict used for denoting phantomJScloud special casing or file type
        """
        logger.info(f"Retrieving {data_url}")

        # if we need to just download the file, don't use phantomjscloud
        if state_config and state_config.get('file'):
            logger.info(f"Downloading file from {data_url}")
            response = requests.get(data_url)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                return
            else:
                logger.error(f'Response status code: {response.status_code}')
                raise ValueError(f'Could not retrieve URL: {data_url}')

        data = {
            'url': data_url,
            'renderType': 'png',
        }

        if state_config:
            # update data with state_config minus message
            message = state_config.pop('message')
            logger.info(message)
            data.update(state_config)

        logger.info('Posting request...')
        response = requests.post(self.phantomjs_url, json.dumps(data))
        logger.info('Done.')

        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f'Response status code: {response.status_code}')
            raise ValueError(f'Could not retrieve URL: {data_url}')

    def timestamped_filename(self, state, suffix='', fileext='png'):
        # basename will be e.g. 'CA' if no suffix, or 'CA-secondary' if suffix is 'secondary'
        state_with_modifier = state if len(suffix) == 0 else '%s-%s' % (state, suffix)
        timestamp = datetime.now(timezone('US/Eastern')).strftime("%Y%m%d-%H%M%S")
        return "%s-%s.%s" % (state_with_modifier, timestamp, fileext)

    def get_s3_path(state, suffix='', fileext='png'):
        filename = self.timestamped_filename(state, suffix, fileext=fileext)
        # CDC goes into its own top-level folder to not mess with state_screenshots
        if state == 'CDC':
            return os.path.join(state, filename)
        else:
            return os.path.join('state_screenshots', state, filename)

    def screenshot(self, state, data_url, suffix='', backup_to_s3=False):
        """Screenshots state data site.

        Parameters
        ----------
        state : str
            Two-letter abbreviation of the state or territory

        data_url : str
            URL containing data site to screenshot

        suffix : str
            If present, will be used in the resulting local and S3 filename (STATE_suffix)

        backup_to_s3 : bool
            If true, will push to S3. If false, backup will be only local
        """

        logger.info(f"Screenshotting {state} {suffix} from {data_url}")
        state_config = self.get_state_config(state, suffix)

        # use specified file extension if it exists, otherwise default to .png
        if state_config and 'file' in state_config:
            fileext = state_config['file']
        else:
            fileext = 'png'

        timestamped_filename = self.timestamped_filename(state, suffix=suffix, fileext=fileext)
        local_path = os.path.join(self.local_dir, timestamped_filename)
        self.save_url_image_to_path(state, data_url, local_path, state_config)
        if backup_to_s3:
            logger.info(f"push to s3")
            self.s3_backup.upload_file(local_path, state)


def load_state_urls(args):
    # get states info from API
    url = 'https://covidtracking.com/api/states/info.csv'
    content = requests.get(url).content
    state_info_df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    
    # if states are user-specified, snapshot only those
    if args.states:
        logger.info(f'Snapshotting states {args.states}')
        states_list = args.states.split(',')
        state_info_df = state_info_df[state_info_df.state.isin(states_list)]
    else:
        logger.info('Snapshotting all states')

    state_urls = {}
    for idx, r in state_info_df.iterrows():
        state_urls[r["state"]] = {
            'primary': r["covid19Site"],
            'secondary': r["covid19SiteSecondary"],
            'tertiary': r["covid19SiteTertiary"],
            'quaternary': r["covid19SiteQuaternary"],
            'quinary': r["covid19SiteQuinary"],
        }

    return state_urls


def load_other_urls_from_spreadsheet(args):
    if args.ltc_urls:
        csv_url = 'https://docs.google.com/spreadsheets/d/1kB6lT0n4wJ2l8uP-lIOZyIVWCRJTPWLGf3Q4ZCC6pMQ/gviz/tq?tqx=out:csv&sheet=LTC_Screencap_Links'
    elif args.crdt_urls:
        csv_url =  'https://docs.google.com/spreadsheets/d/1boHD1BxuZ2UY7FeLGuwXwrb8rKQLURXsmNAdtDS-AX0/gviz/tq?tqx=out:csv&sheet=Sheet1' 
    urls_df = pd.read_csv(csv_url)

    # if states are user-specified, snapshot only those
    if args.states:
        logger.info(f'Snapshotting states {args.states}')
        states_list = args.states.split(',')
        urls_df = urls_df[urls_df.State.isin(states_list)]
    else:
        logger.info('Snapshotting all states')

    state_urls = {}
    for idx, r in urls_df.iterrows():
        state_urls[r['State']] = {
            'primary': r['Link 1'],
            'secondary': r['Link 2'],
            'tertiary': r['Link 3'],
        }

    return state_urls


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)
    s3 = S3Backup(bucket_name=args.s3_bucket, s3_subfolder=args.s3_subfolder)

    # load the config for this run
    if args.core_urls:
        config_basename = 'core_screenshot_config.yaml'
    elif args.crdt_urls:
        config_basename = 'crdt_screenshot_config.yaml'
    elif args.ltc_urls:
        config_basename = 'ltc_screenshot_config.yaml'

    screenshot_config_path = os.path.join(os.path.dirname(__file__), config_basename)
    with open(screenshot_config_path) as f:
        config = yaml.safe_load(f)

    screenshotter = Screenshotter(
        local_dir=args.temp_dir, s3_backup=s3,
        phantomjscloud_key=args.phantomjscloud_key, config=config)

    if args.core_urls:
        state_urls = load_state_urls(args)
    else:
        state_urls = load_other_urls_from_spreadsheet(args)

    failed_states = []
    for state, urls in state_urls.items():
        data_url = urls.get('primary')
        secondary_data_url = urls.get('secondary')
        tertiary_data_url = urls.get('tertiary')
        quaternary_data_url = urls.get('quaternary')
        quinary_data_url = urls.get('quinary')

        try:
            if not pd.isnull(data_url):
                screenshotter.screenshot(
                    state, data_url,
                    backup_to_s3=args.push_to_s3)
            if not pd.isnull(secondary_data_url):
                screenshotter.screenshot(
                    state, secondary_data_url, suffix='secondary',
                    backup_to_s3=args.push_to_s3)
            if not pd.isnull(tertiary_data_url):
                screenshotter.screenshot(
                    state, tertiary_data_url, suffix='tertiary',
                    backup_to_s3=args.push_to_s3)
            if not pd.isnull(quaternary_data_url):
                screenshotter.screenshot(
                    state, quaternary_data_url, suffix='quaternary',
                    backup_to_s3=args.push_to_s3)
            if not pd.isnull(quinary_data_url):
                screenshotter.screenshot(
                    state, quinary_data_url, suffix='quinary',
                    backup_to_s3=args.push_to_s3)
        except:
            failed_states.append(state)

    if failed_states:
        logger.error(f"Failed states for this run: {','.join(failed_states)}")
    else:
        logger.info("All required states successfully screenshotted")

    # special-case: screenshot CDC "US Cases" and "US COVID Testing" tabs. Do this as part of the
    # CRDT run, which is less frequent
    if args.crdt_urls:
        screenshotter.screenshot(
            'CDC', 'https://www.cdc.gov/covid-data-tracker/#testing', suffix='testing',
            backup_to_s3=args.push_to_s3)

        screenshotter.screenshot(
            'CDC', 'https://www.cdc.gov/covid-data-tracker/', suffix='cases',
            backup_to_s3=args.push_to_s3)


if __name__ == "__main__":
    main()
