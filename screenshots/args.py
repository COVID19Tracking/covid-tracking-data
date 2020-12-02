""" CLI argument definitions for the screenshotter. This module defines the argument parser. """

from argparse import ArgumentParser, RawDescriptionHelpFormatter


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

parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
    help='If present, will only print the resulting PhantomJScloud request')

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

# Allows the user to specify primary, secondary, etc. screenshots to take
# If none of these arguments are present, all screenshots will be taken
screenshot_type_group = parser.add_argument_group('which_screenshots')

screenshot_type_group.add_argument('--primary', dest='primary', action='store_true',
    default=False, help='Run the primary screenshot')
screenshot_type_group.add_argument('--secondary', dest='secondary', action='store_true',
    default=False, help='Run the secondary screenshot')
screenshot_type_group.add_argument('--tertiary', dest='tertiary', action='store_true',
    default=False, help='Run the tertiary screenshot')
screenshot_type_group.add_argument('--quaternary', dest='quaternary', action='store_true',
    default=False, help='Run the quaternary screenshot')
screenshot_type_group.add_argument('--quinary', dest='quinary', action='store_true',
    default=False, help='Run the quinary screenshot')

# Args relating to Slack notifications
parser.add_argument(
    '--slack-channel',
    default='',
    help='Slack channel ID to notify on screenshot errors')

parser.add_argument(
    '--slack-api-token',
    default='',
    help='Slack API token to use for notifications')
