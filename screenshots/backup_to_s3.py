""" Main sript to run image capture screenshots for state data pages. """

import io
import os
import sys

from loguru import logger
import pandas as pd
import requests
import yaml

from args import parser as screenshots_parser
from screenshots import Screenshotter, S3Backup, SlackNotifier


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
        csv_url =  'https://docs.google.com/spreadsheets/d/1lfwMmo7q-faKfvh6phxQs9rEJXVnnyISFtiVbq9XJ7U/gviz/tq?tqx=out:csv&sheet=Sheet1' 
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


def config_from_args(args):
    # load the config for this run
    if args.core_urls:
        config_basename = 'core_screenshot_config.yaml'
    elif args.crdt_urls:
        config_basename = 'crdt_screenshot_config.yaml'
    elif args.ltc_urls:
        config_basename = 'ltc_screenshot_config.yaml'

    screenshot_config_path = os.path.join(os.path.dirname(__file__), 'configs', config_basename)
    with open(screenshot_config_path) as f:
        config = yaml.safe_load(f)

    return config


def state_urls_from_args(args):
    if args.core_urls:
        return load_state_urls(args)
    else:
        return load_other_urls_from_spreadsheet(args)


def slack_notifier_from_args(args):
    if args.slack_channel and args.slack_api_token:
        return SlackNotifier(args.slack_channel, args.slack_api_token)
    return None


# Return a small string describing which run this is: core, CRDT, LTC.
def run_type_from_args(args):
    if args.core_urls:
        run_type = 'core'
    elif args.crdt_urls:
        run_type = 'CRDT'
    else:
        run_type = 'LTC'
    return run_type


# This is a special-case function: we're screenshotting IHS data separately for now
def screenshot_IHS(args):
    s3 = S3Backup(bucket_name=args.s3_bucket, s3_subfolder='IHS')
    screenshotter = Screenshotter(
        local_dir=args.temp_dir, s3_backup=s3,
        phantomjscloud_key=args.phantomjscloud_key, config=config_from_args(args))
    data_url = 'https://www.ihs.gov/coronavirus/'
    try:
        screenshotter.screenshot('IHS', data_url, suffix='', backup_to_s3=args.push_to_s3)
    except ValueError as e:
        logger.error('IHS screenshot failed: %s' % e)


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = screenshots_parser.parse_args(args_list)
    s3 = S3Backup(bucket_name=args.s3_bucket, s3_subfolder=args.s3_subfolder)

    config = config_from_args(args)
    state_urls = state_urls_from_args(args)
    slack_notifier = slack_notifier_from_args(args)
    run_type = run_type_from_args(args)
    screenshotter = Screenshotter(
        local_dir=args.temp_dir, s3_backup=s3,
        phantomjscloud_key=args.phantomjscloud_key, config=config)

    failed_states = []
    slack_failure_messages = []
    for state, urls in state_urls.items():

        # returns True if this particular screenshotter run succeeded, false otherwise: exists to
        # not crash on exceptions, and keep track of which screenshots failed
        def screenshotter_succeeded(data_url, suffix):
            if pd.isnull(data_url):
                return True  # trivial success

            # try 4 times in case of intermittent issues
            err = None
            for i in range(4):
                try:
                    screenshotter.screenshot(
                        state, data_url, suffix=suffix,
                        backup_to_s3=args.push_to_s3)
                    return True
                except ValueError as e:
                    err = e
                    logger.error(e)

            # if we're here, all attempts failed, notify Slack
            if slack_notifier:
                suffix_str = suffix or 'primary'
                slack_failure_messages.append(
                    f"Error in {state} {suffix_str}: {err}")
            return False

        # Retrieve set of URLs to load. If user didn't specify screenshot(s) to take, take them all
        if not (args.primary or args.secondary or args.tertiary or args.quaternary or args.quinary):
            urls_with_suffixes = [
                (urls.get('primary'), ''),
                (urls.get('secondary'), 'secondary'),
                (urls.get('tertiary'), 'tertiary'),
                (urls.get('quaternary'), 'quaternary'),
                (urls.get('quinary'), 'quinary'),
            ]
        else:
            urls_with_suffixes = []
            for attr_name in ['primary', 'secondary', 'tertiary', 'quaternary', 'quinary']:
                if getattr(args, attr_name) is True:
                    suffix = '' if attr_name == 'primary' else attr_name
                    urls_with_suffixes.append((urls.get(attr_name), suffix))

        # Take screenshots, keeping track of which ones failed
        for (data_url, suffix) in urls_with_suffixes:
            success = screenshotter_succeeded(data_url, suffix)
            if not success:
                failed_states.append((state, suffix or 'primary'))

    if failed_states:
        failed_states_str = ', '.join([':'.join(x) for x in failed_states])
        logger.error(f"Errored screenshot states for this {run_type} run: {failed_states_str}")
        if slack_notifier:
            slack_response = slack_notifier.notify_slack(
                f"Errored screenshot states for this {run_type} run: {failed_states_str}")
            # put the corresponding messages into a thread
            thread_ts = slack_response.get('ts')
            for detailed_message in slack_failure_messages:
                slack_notifier.notify_slack(detailed_message, thread_ts=thread_ts)
    else:
        logger.info("All attempted states successfully screenshotted")

    # special-case: screenshot IHS data once a day, so attach it to the LTC run
    if run_type == 'LTC':
        screenshot_IHS(args)


if __name__ == "__main__":
    main()
