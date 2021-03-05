from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import datetime
import sys

"""Federal data combiner tool. Downloads federal testing, hospitalization, and case/death data and combines it
into unified state-level output. 

This script outputs a csv file named federal-covid-data-DATE.csv and is intended to be run in the Google Colab 
environment, but passing the 'STDOUT' argument will output to STDOUT instead."""

HHS_TESTING_METADATA_URL = "https://healthdata.gov/api/3/action/package_show?id=c13c00e3-f3d0-4d49-8c43-bf600a6c0a0d&page=0"
HHS_HOSPITALIZATION_TIMESERIES_METADATA_URL = "https://healthdata.gov/api/3/action/package_show?id=83b4a668-9321-4d8c-bc4f-2bef66c49050&page=0"
HHS_HOSPITALIZATION_REVISIONS_URL = "https://healthdata.gov/node/3281086/revisions"
HHS_HOSPITALIZATION_CURRENT_URL = "https://healthdata.gov/dataset/covid-19-reported-patient-impact-and-hospital-capacity-state"
CDC_CASE_DEATH_URL = "https://data.cdc.gov/api/views/9mfq-cb36/rows.csv?accessType=DOWNLOAD"


def get_hospitalization_csv_urls():
    """get a set of recent revisions for the HHS hospitalizations-by-state dataset"""
    req = requests.get(HHS_HOSPITALIZATION_REVISIONS_URL)
    soup = BeautifulSoup(req.content, 'html.parser')

    # find all past revision elements from the page
    elems = soup.select('tr.diff-revision a[href*=revisions]')
    # need to start with the current revision since it's not in the below list
    revision_urls = [HHS_HOSPITALIZATION_CURRENT_URL]
    for elem in elems:
        revision_urls.append(f"https://healthdata.gov{elem['href']}")
    # go through the top revisions and get the CSV download URL for each one
    csv_urls = []
    for url in revision_urls[0:min(8, len(revision_urls) - 1)]:
        req = requests.get(url)
        soup = BeautifulSoup(req.content, 'html.parser')
        if "/revisions/" in url:
            csv_urls.append(soup.select_one('div.download a')['href'])
        else:
            csv_urls.append(soup.select_one('a.data-link')['href'])
    return csv_urls


def get_hospitalization_dailies():
    """build a dataframe containing the combination of several days of recent HHS hospitalization daily data"""
    csv_urls = get_hospitalization_csv_urls()
    data_frames = []
    seen_dates = set()

    for url in csv_urls:
        date = re.search("utilization_(\d+)_\d+\.csv", url).group(1)
        if date in seen_dates:  # don't add the same date twice if it comes up
            continue
        seen_dates.add(date)
        data = pd.read_csv(url)
        data['date'] = date
        data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
        data_frames.append(data)
    hospitalization_dailies = pd.concat(data_frames)
    hospitalization_dailies.set_index(['state', 'date'])
    return hospitalization_dailies


# request the dataset metadata and pull out the csv data url inside
testing_metadata_req = requests.get(HHS_TESTING_METADATA_URL)
testing_metadata = testing_metadata_req.json()
testing_url = testing_metadata["result"][0]["resources"][0]["url"]

hospitalization_metadata_req = requests.get(HHS_HOSPITALIZATION_TIMESERIES_METADATA_URL)
hospitalization_metadata = hospitalization_metadata_req.json()
hospitalization_url = hospitalization_metadata["result"][0]["resources"][0]["url"]

case_death_url = CDC_CASE_DEATH_URL

# download and parse all three data files
[testing, hospitalization, case_death] = [pd.read_csv(url) for url in
                                          [testing_url, hospitalization_url, case_death_url]]

# testing data comes out with one row per state/date/outcome combination.
# unpack that and squash it into one row per state/date only
testing = testing.set_index(['state', 'date', 'overall_outcome']).unstack(level=-1)
testing = testing[['new_results_reported', 'total_results_reported']]
testing.columns = ['_'.join(tup).rstrip('_') for tup in testing.columns.values]
testing = testing.reset_index()
testing['date'] = pd.to_datetime(testing['date'], format='%Y-%m-%d')

# the HHS hospitalization time series is only updated weekly. To compensate, we download the latest daily data
# and merge it on top of the weekly data, taking only the most recent values for a given state/date
hospitalization['date'] = pd.to_datetime(hospitalization['date'], format='%Y-%m-%d')
hospitalization_dailies = get_hospitalization_dailies()
# we want to use the HHS weekly time series up until its last day, then fill in the rest of the data from the daily
# files. we overwrite the last day of the time series with the dailies because the dailies come out after the weekly
hospitalization_dailies = hospitalization_dailies[hospitalization_dailies['date'] >= hospitalization['date'].max()]
hospitalization.set_index(['state', 'date'])
hospitalization = hospitalization.merge(hospitalization_dailies, how='outer')
# the keep='last' here keeps just the daily data when both duplicate weekly and daily data exist
hospitalization = hospitalization.drop_duplicates(subset=['date', 'state'], keep='last', ignore_index=True)
hospitalization = hospitalization[
    ['state', 'date', 'previous_day_admission_adult_covid_confirmed', 'previous_day_admission_adult_covid_suspected',
     'total_adult_patients_hospitalized_confirmed_and_suspected_covid',
     'total_adult_patients_hospitalized_confirmed_covid']]
# HHS hospitalization data becomes usable on 7/15/20
hospitalization = hospitalization.query('date >= 20200715')

# case/death data: pick a subset of columns and prepare to merge
case_death = case_death[
    ['submission_date', 'state', 'tot_cases', 'conf_cases', 'prob_cases', 'new_case', 'pnew_case', 'tot_death',
     'conf_death', 'prob_death', 'new_death', 'pnew_death']]
case_death = case_death.rename(columns={'submission_date': 'date'})

# merge all the dataframes together into one big combination
combined = pd.merge(left=testing, right=hospitalization, on=['state', 'date'], how='outer')

case_death['date'] = pd.to_datetime(case_death['date'], format='%m/%d/%Y')
combined['date'] = pd.to_datetime(combined['date'], format='%Y-%m-%d')

combined = combined.merge(case_death, on=['state', 'date'], how='outer')

combined.sort_values(by=['date', 'state'], inplace=True, ignore_index=True)

# and output the data
outfile_name = f"federal-covid-data-{datetime.datetime.today().strftime('%Y%m%d')}.csv"
if "STDOUT" in sys.argv[1:]:  # allow optional output to STDOUT instead of a file
    outfile_name = sys.stdout
combined.to_csv(outfile_name, index=False)

# tell Google Colab to have the user download the output
# or do nothing if we're not in a Colab environment
try:
    from google.colab import files
    files.download(outfile_name)
except ModuleNotFoundError:
    pass
