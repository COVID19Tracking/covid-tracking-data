from tableauscraper import TableauScraper as TS
from itertools import repeat
from datetime import datetime
from pytz import timezone

"""Fetch Kansas's Tableau LTC dashboard and output the data table data to STDOUT"""

url = "https://public.tableau.com/views/COVID-19TableauVersion2/ClusterSummary"

ts = TS()
ts.loads(url)
dashboard = ts.getDashboard()
t = dashboard.getWorksheet("Active Outbreak Locations")
df = t.data

# filter only for long-term care facilities and extract the data we need
df = df[df['Type-value'].eq("Long Term Care Facility")]
out_data = df.reindex(columns=["date_collected",
                               "state",
                               "County-alias",
                               "City or State-alias",
                               "Facility-value",
                               "Type-value",
                               "Last Onset Date-value",
                               "SUM(Number of Cases within 14 days)-alias",
                               "blank"])

out_data['date_collected'] = datetime.now(timezone('US/Eastern')).strftime('%Y%m%d')
out_data['state'] = 'KS'

# output the dataframe in CSV format to match the facility data entry sheet
out_columns = ["date_collected",
               "state",
               "County-alias",
               "City or State-alias",
               "Facility-value",
               "Type-value"]
out_columns.extend(repeat("blank", 4))
out_columns.append("Last Onset Date-value")
out_columns.extend(repeat("blank", 23))
out_columns.append("SUM(Number of Cases within 14 days)-alias")

print(out_data.to_csv(index=False, columns=out_columns))
