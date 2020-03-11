from argparse import ArgumentParser
import json
import os.path
import requests
import sys
import tempfile

from github import Github
from github.GithubException import UnknownObjectException
import pandas as pd


parser = ArgumentParser()

parser.add_argument(
    '--github-access-token',
    default='',
    help='GitHub access token string for covid-tracking-data repo')

REPO_NAME = 'COVID19Tracking/covid-tracking-data'

API_URLS = {
    'states_current': 'https://covid.cape.io/states',
    'states_daily_4pm_et': 'https://covid.cape.io/states/daily',
    'states_info': 'https://covid.cape.io/states/info',
    'us_current': 'https://covid.cape.io/us',
    'us_daily': 'https://covid.cape.io/us/daily',
    'counties': 'https://covid.cape.io/counties',
}

def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)

    github = Github(args.github_access_token)
    repo = github.get_repo(REPO_NAME)

    for name, url in API_URLS.items():
        json_contents = requests.get(url).json()
        df = pd.DataFrame(json_contents, columns=json_contents[0].keys())
        gh_filename = 'data/%s.csv' % name

        with tempfile.NamedTemporaryFile() as f:
            df.to_csv(f.name, index=False)
            with open(f.name) as df_f:
                new_contents = df_f.read()
            try:
                current_contents = repo.get_contents(gh_filename, ref='master')
                print('Updating %s...' % name)
                repo.update_file(
                    gh_filename, 'Updating %s' % gh_filename, new_contents, current_contents.sha)
            except UnknownObjectException:
                # new file, not an update
                print('Making a new file for for %s...' % name)
                repo.create_file(
                    gh_filename, 'Creating %s' % gh_filename, new_contents)

    print('Done!')


if __name__ == "__main__":
    main()
