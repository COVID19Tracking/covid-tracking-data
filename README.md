# COVID Tracking Data (CSV)

**Do not use this repository to download or display data**. Use the [COVID Tracking API](https://covidtracking.com/api) instead.

Hourly updated repository with CSV representations of data from the [Covid Tracking API](https://covidtracking.com/api) - see link for details on each field. Since this repository may be an hour behind our API, please use the API directly if you need the most recent data.

For information about the project and how this data is collected, see the COVID Tracking Project [website](https://www.covidtracking.com) and [Twitter account](https://twitter.com/COVID19Tracking).

## CSV data files

* States current - https://github.com/julia326/covid-tracking-data/blob/master/data/states_current.csv
* States daily 4 pm ET - https://github.com/julia326/covid-tracking-data/blob/master/data/states_daily_4pm_et.csv
* States info - https://github.com/julia326/covid-tracking-data/blob/master/data/states_info.csv
* US current - https://github.com/julia326/covid-tracking-data/blob/master/data/us_current.csv
* US daily - https://github.com/julia326/covid-tracking-data/blob/master/data/us_daily.csv
* Counties - https://github.com/julia326/covid-tracking-data/blob/master/data/counties.csv

## Running the script

For the list of options, type:

```bash session
> python ./backup_to_s3.py --help
```

This will give you a list of options for running the script:

```bash
usage: backup_to_s3.py [-h] [--temp-dir TEMP_DIR] [--s3-bucket S3_BUCKET]
                       [--states STATES] [--public-only] [--push-to-s3]
                       [--replace-most-recent-snapshot]
                       [--phantomjscloud-key PHANTOMJSCLOUD_KEY]

Script to run image capture screenshots for state data pages.

optional arguments:
  -h, --help            show this help message and exit
  --temp-dir TEMP_DIR   Local temp dir for snapshots
  --s3-bucket S3_BUCKET
                        S3 bucket name
  --states STATES       Comma-separated list of state 2-letter names. If
                        present, will only screenshot those.
  --public-only         If present, will only snapshot public website and not
                        state pages
  --push-to-s3          Push screenshots to S3
  --replace-most-recent-snapshot
                        If present, will first delete the most recent snapshot
                        for the state before saving new screenshot to S3
  --phantomjscloud-key PHANTOMJSCLOUD_KEY
                        API key for PhantomJScloud, used for browser image
                        capture                       
```                       
