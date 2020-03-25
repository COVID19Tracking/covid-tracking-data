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


parser = ArgumentParser(
    description=__doc__,
    formatter_class=RawDescriptionHelpFormatter)

parser.add_argument(
    '--temp-dir',
    default='/tmp/public-cache',
    help='Local temp dir for snapshots')

parser.add_argument(
    '--s3-bucket',
    default='covid-data-archive',
    help='S3 bucket name')

parser.add_argument('--states',
    default='',
    help='Comma-separated list of state 2-letter names. If present, will only screenshot those.')

parser.add_argument('--public-only', action='store_true', default=False,
    help='If present, will only snapshot public website and not state pages')

parser.add_argument('--push-to-s3', dest='push_to_s3', action='store_true', default=False,
    help='Push screenshots to S3')

parser.add_argument('--replace-most-recent-snapshot', action='store_true', default=False,
    help='If present, will first delete the most recent snapshot for the state before saving ' 
         'new screenshot to S3')

parser.add_argument('--phantomjscloud-key', default='',
    help='API key for PhantomJScloud, used for browser image capture')


class S3Backup():

    def __init__(self, bucket_name: str):
        self.s3 = boto3.resource('s3')
        self.bucket_name = bucket_name
        self.bucket = self.s3.Bucket(self.bucket_name)

    # for now just uploads image (PNG) file with specified name
    def upload_file(self, local_path: str, s3_path: str):
        self.s3.meta.client.upload_file(
            local_path, self.bucket_name, s3_path,
            ExtraArgs={'ContentType': 'image/png'})

    def delete_most_recent_snapshot(self, state: str):
        state_file_keys = [file.key for file in self.bucket.objects.all() if state in file.key]
        most_recent_state_key = sorted(state_file_keys, reverse=True)[0]
        self.s3.Object(self.bucket_name, most_recent_state_key).delete()


class Screenshotter():

    def __init__(self, local_dir, s3_backup, phantomjscloud_key):
        self.phantomjs_url = 'https://phantomjscloud.com/api/browser/v2/%s/' % phantomjscloud_key
        self.local_dir = local_dir
        self.s3_backup = s3_backup

    # makes a PhantomJSCloud call to data_url and saves the .png output to specified path
    def save_url_image_to_path(self, state, data_url, path):
        logger.info(f"Retrieving {data_url}")

        data = {
            'url': data_url,
            'renderType': 'png',
        }

        # PhantomJScloud gets the page length wrong for some states, need to set those manually
        if state in ['ID', 'PA', 'IN']:
            logger.info(f"using larger viewport for state {state}")
            data['renderSettings'] = {'viewport': {'width': 1400, 'height': 3000}}
        elif state in ['NE']:
            # really huge viewport for some reason
            logger.info(f"using huge viewport for state {state}")
            data['renderSettings'] = {'viewport': {'width': 1400, 'height': 5000}}

        logger.info('Posting request...')
        response = requests.post(self.phantomjs_url, json.dumps(data))
        logger.info('Done.')

        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f'Failed to retrieve URL: {data_url}')
            raise

    @staticmethod
    def timestamped_filename(state):
        timestamp = datetime.now(timezone('US/Eastern')).strftime("%Y%m%d-%H%M%S")
        return "%s-%s.png" % (state, timestamp)

    @staticmethod
    def get_s3_path(state):
        filename = Screenshotter.timestamped_filename(state)
        return os.path.join('state_screenshots', state, filename)

    def get_local_path(self, state):
        filename = Screenshotter.timestamped_filename(state)
        return os.path.join(self.local_dir, filename)

    def screenshot(self, state, data_url,
            backup_to_s3=False, replace_most_recent_snapshot=False):
        logger.info(f"Screenshotting {state} from {data_url}")
        local_path = self.get_local_path(state)
        self.save_url_image_to_path(state, data_url, local_path)
        if backup_to_s3:
            s3_path = self.get_s3_path(state)
            if replace_most_recent_snapshot:
                logger.info(f"    3a. first delete the most recent snapshot")
                self.s3_backup.delete_most_recent_snapshot(state)
            logger.info(f"    4. push to s3 at {s3_path}")
            self.s3_backup.upload_file(local_path, s3_path)


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)

    s3 = S3Backup(bucket_name=args.s3_bucket)
    screenshotter = Screenshotter(
        local_dir=args.temp_dir, s3_backup=s3, phantomjscloud_key=args.phantomjscloud_key)

    # get states info from API
    url = 'https://covidtracking.com/api/states/info.csv'
    content = requests.get(url).content
    state_info_df = pd.read_csv(io.StringIO(content.decode('utf-8'))).fillna(0)
    
    failed_states = []

    # screenshot public state site
    screenshotter.screenshot(
        'public',
        'https://covidtracking.com/data/',
        backup_to_s3=args.push_to_s3,
        replace_most_recent_snapshot=args.replace_most_recent_snapshot)

    if args.public_only:
        logger.info("Not snapshotting state pages, was asked for --public-only")
        return

    # screenshot state images
    if args.states:
        states = args.states.split(',')
        for state in states:
            data_url = state_info_df.loc[state_info_df.state == state].head(1).covid19Site.values[0]
            try:
                screenshotter.screenshot(
                    state, data_url,
                    backup_to_s3=args.push_to_s3,
                    replace_most_recent_snapshot=args.replace_most_recent_snapshot)
            except:
                failed_states.append(state)

    else:
        for idx, r in state_info_df.iterrows():
            state = r["state"]
            data_url = r["covid19Site"]
            try:
                screenshotter.screenshot(
                    state, data_url,
                    backup_to_s3=args.push_to_s3,
                    replace_most_recent_snapshot=args.replace_most_recent_snapshot)
            except:
                failed_states.append(state)

    if failed_states:
        logger.error(f"Failed states for this run: {','.join(failed_states)}")
    else:
        logger.error("All required states successfully screenshotted")


if __name__ == "__main__":
    main()
