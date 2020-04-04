#!/bin/bash
#
# This script refreshes the CSV backups from the public Google spreadsheet at
# covidtracking.com/sheets and pushes the changes to GitHub.

set -ex

REPO=$HOME/code/covid-tracking-data

curl https://covidtracking.com/api/v1/states/current.csv -o $REPO/data/states_current.csv
curl https://covidtracking.com/api/v1/states/daily.csv -o $REPO/data/states_daily_4pm_et.csv
curl https://covidtracking.com/api/v1/states/info.csv -o $REPO/data/states_info.csv
curl https://covidtracking.com/api/us.csv -o $REPO/data/us_current.csv
curl https://covidtracking.com/api/us/daily.csv -o $REPO/data/us_daily.csv
curl https://covidtracking.com/api/counties.csv -o $REPO/data/counties.csv

# any changes in data/*.csv files within repo?
if [[ `git -C $REPO diff --exit-code $REPO/data/*.csv` ]]; then
    echo 'updating at least one data CSV...'
    # add and commit any changes
    git -C $REPO add $REPO/data/*.csv
    git -C $REPO commit -m 'Updating public spreadsheet CSV backups'
    git -C $REPO push
    echo 'done'
else
    echo 'no news, not updating'
fi
