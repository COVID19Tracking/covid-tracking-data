"""Notify Slack about screenshot errors"""

from loguru import logger
from slack import WebClient
from slack.errors import SlackApiError


SLACK_CHANNEL = 'C01D98JCTFB'
SLACK_API_TOKEN = 'xoxb-975992389859-1019087916167-Co72eTBZ62ArPfw4B1JxSM5z'


class SlackNotifier():

    def __init__(self, slack_channel, slack_api_token):
        self.channel = slack_channel
        self.client = WebClient(token=slack_api_token)

    def notify_slack(self, message):
        try:
            response = client().chat_postMessage(
                channel=channel(),
                text=message
            )
        except SlackApiError as e:
            # just log Slack failures but don't break on them
            logger.error("Could not notify Slack, received error: %s" % e.response["error"])