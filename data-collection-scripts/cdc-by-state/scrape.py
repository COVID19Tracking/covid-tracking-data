"""NOTE: this is meant to be run from the top-level repo directory.
"""

import json
import pandas as pd
import requests


STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


def scrape():
    for state in STATES:
        print('Processing %s' % state)
        url = 'https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=integrated_county_timeseries_state_%s_external' % state
        result_json = json.loads(requests.get(url).text)
        df = pd.DataFrame(result_json['integrated_county_timeseries_external_data'])
        path = 'data/cdc_by_state/%s_integrated_county_timeseries.csv' % state
        df.to_csv(path, index=False)


scrape()
