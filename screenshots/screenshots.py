""" Supporting classes for taking screenshots and saving them to S3."""

from datetime import datetime
import json
import os
from pytz import timezone

import boto3
from loguru import logger
import requests
from slack import WebClient
from slack.errors import SlackApiError


class Screenshotter():

    def __init__(self, local_dir, s3_backup, phantomjscloud_key, config, dry_run=False):
        self.phantomjs_url = 'https://phantomjscloud.com/api/browser/v2/%s/' % phantomjscloud_key
        self.local_dir = local_dir
        self.s3_backup = s3_backup
        self.config = config
        self.dry_run = dry_run

    def get_state_config(self, state, suffix):
        # primary is denoted with no suffix, but the section is called "primary" in the YAML config
        if suffix == '':
            return self.config['primary'].get(state)
        for possible_suffix in ['secondary', 'tertiary', 'quaternary', 'quinary']:
            if suffix == possible_suffix and self.config[possible_suffix]:
                return self.config[possible_suffix].get(state)
        
        return None

    # makes a PhantomJSCloud call to data_url and saves the output to specified path
    def save_url_image_to_path(self, state, data_url, path, state_config=None, suffix=None):
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

        suffix : str
            e.g. primary, secondary, etc.
        """
        logger.info(f"Retrieving {data_url}")

        # if we need to just download the file, don't use phantomjscloud
        if state_config and state_config.get('file'):
            if self.dry_run:
                logger.warning(f'Dry run: Downloading {state} {suffix} file from {data_url}')
                return

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
            state_config_copy = state_config.copy()
            message = state_config_copy.pop('message')
            logger.info(message)
            data.update(state_config_copy)

        # set maxWait if unset
        if 'requestSettings' in data:
            if 'maxWait' not in data['requestSettings']:
                data['requestSettings']['maxWait'] = 60000
        else:
            data['requestSettings'] = {'maxWait': 60000}

        if self.dry_run:
            logger.warning(f'Dry run: PhantomJsCloud request for {state} {suffix} from {data_url}: {json.dumps(data)}')
            return

        logger.info('Posting request %s...' % data)
        response = requests.post(self.phantomjs_url, json.dumps(data))
        logger.info('Done.')

        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f'Response status code: {response.status_code}')
            if 'meta' in response.json():
                response_metadata = response.json()['meta']
                raise ValueError(f'Could not retrieve URL {data_url}, got response metadata {response_metadata}')
            else:
                raise ValueError(
                    'Could not retrieve URL %s and response has no metadata. Full response: %s' % (
                        data_url, response.json()))

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
        self.save_url_image_to_path(state, data_url, local_path, state_config, suffix or 'primary')
        if backup_to_s3:
            logger.info(f"push to s3")
            self.s3_backup.upload_file(local_path, state)


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


class SlackNotifier():

    def __init__(self, slack_channel, slack_api_token):
        self.channel = slack_channel
        self.client = WebClient(token=slack_api_token)

    # Returns the SlackResponse object
    def notify_slack(self, message, thread_ts=None):
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                thread_ts=thread_ts
            )
            return response
        except SlackApiError as e:
            # just log Slack failures but don't break on them
            logger.error("Could not notify Slack, received error: %s" % e.response["error"])
