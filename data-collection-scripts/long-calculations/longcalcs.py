import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
from pytz import timezone as tz  # replace with ZoneInfo once G upgrades to 3.9
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import re
import zipfile


# DE positives
def de(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	df = pd.read_csv('https://myhealthycommunity.dhss.delaware.gov/locations/state/download_covid_19_data')
	df = df[df['Unit'] == 'tests'].set_index(['Year', 'Month', 'Day']).sort_index()
	print(df.loc[df.index.unique()[-3]][['Statistic', 'Value']], file=f)
	print("\n\n", file=f)


# HI PCR Test Encounters and update time
def hi(f):
	# HI PCR Test Encounters
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	hi = pd.read_csv("https://public.tableau.com/views/EpiCurveApr4/CSVDownload.csv?:showVizHome=no")
	print(hi.select_dtypes(exclude=['object']).sum(), file=f)

	# HI updated time
	res = requests.get("https://services9.arcgis.com/aKxrz4vDVjfUwBWJ/arcgis/rest/services/HIEMA_TEST_DATA_PUBLIC_LATEST/FeatureServer/0/query?where=name%3D'State'&returnGeometry=false&outFields=*&orderByFields=reportdt desc&resultOffset=0&resultRecordCount=1&f=json")
	updated = datetime.fromtimestamp(res.json()['features'][0]['attributes']['reportdt']/1000) # because ms
	# format we want: 12/27/2020 8:30:00
	print("\nUpdate time: ", updated.replace(tzinfo=timezone.utc).astimezone(tz=tz("Pacific/Honolulu")).strftime("%m/%d/%Y %H:%M:%S"), file=f)
	print("\n\n", file=f)


# MA
def ma(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	url = 'https://www.mass.gov/info-details/covid-19-response-reporting'
	req = requests.get(url)
	soup = BeautifulSoup(req.text, 'html.parser')
	a = soup.find('a', string=re.compile("COVID-19 Raw Data"))
	link = "https://www.mass.gov{}".format(a['href'])
	print("Download link = ", link, file=f)

	res = requests.get(link)
	tabs = pd.read_excel(res.content, sheet_name=None)

	print("PCR Total People", file=f)
	print(tabs['Testing2 (Report Date)']['Molecular Total'].iloc[-1], "\n", file=f)

	df = tabs['TestingByDate (Test Date)'].filter(like="All Positive")
	print(df.sum(), file=f)
	print("\n\n", file=f)


	# weekly report
	url = 'https://www.mass.gov/info-details/covid-19-response-reporting'
	req = requests.get(url)
	soup = BeautifulSoup(req.text, 'html.parser')
	a = soup.find('a', string=re.compile("Weekly Public Health Report - Raw"))
	link = "https://www.mass.gov{}".format(a['href'])
	print("\nWeekly link = ", link, file=f)
	res = requests.get(link)
	df = pd.read_excel(BytesIO(res.content), sheet_name='Antibody', parse_dates=['Test Date'], index_col='Test Date')
	print(df.sum(), file=f)

	# ever hospitalized
	print('\nEver Hospitalized', "\n", file=f)
	max_date = tabs['RaceEthnicityLast2Weeks']['Date'].max()
	print(tabs['RaceEthnicityLast2Weeks'][tabs['RaceEthnicityLast2Weeks']['Date'] == max_date].sum(), file=f)
	print("\n\n", file=f)


# ME
# make sure that this does not collapse upon printing
def me(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	print(pd.read_csv("https://gateway.maine.gov/dhhs-apps/mecdc_covid/hospital_capacity.csv", nrows=1, usecols=[0,1,2,3]).sum(), file=f)
	print("\n\n", file=f)


# MI Testing
def mi(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	url = 'https://www.michigan.gov/coronavirus/0,9753,7-406-98163_98173---,00.html'

	req = requests.get(url)
	soup = BeautifulSoup(req.text, 'html.parser')
	a = soup.find('a', string="Diagnostic Tests by Result and County")
	mi_link = "https://www.michigan.gov/{}".format(a['href'])
	print("Link = ", mi_link, file=f)

	mi = pd.read_excel(mi_link).drop(columns=['COUNTY'])
	print(mi.sum(), file=f)
	print("\n\n", file=f)


# NC Antigen tests
def nc(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	nc = pd.read_csv("https://public.tableau.com/views/NCDHHS_COVID-19_DataDownload/DailyTestingMetrics.csv", parse_dates=['Date'], index_col='Date', thousands=',')
	print(nc.pivot(columns='Measure Names').sum().astype('int64'), file=f)
	print("\n\n", file=f)


# ND Negatives and Testing
def nd(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	url = "https://static.dwcdn.net/data/NVwou.csv"
	headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0"}
	req = requests.get(url, headers=headers)
	print(pd.read_csv(StringIO(req.text)).filter(like='Negative').sum(), file=f)

	print("\nTesting Data", file=f)
	df = pd.read_csv('https://www.health.nd.gov/sites/www/files/documents/Files/MSS/coronavirus/charts-data/PublicUseData.csv')
	print(df.filter(like='tests').sum(), file=f)
	print("\n\n", file=f)


# OH testing
def oh(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	key_url = "https://data.ohio.gov/apigateway-secure/data-portal/download-file/cba54974-06ab-4ec8-92bc-62a83b40614e?key=2b4420ffc0c5885f7cd42a963cfda0b489a9a6dff49461e1a921b355ee0424c029cf4ff2ee80c8c82ef901d818d71f9def8cba3651f6595bd6a07e1477438b97bbc5d7ccf7b5b66c154779ce7a4f5b83"
	testing_url = "https://data.ohio.gov/apigateway-secure/data-portal/download-file/2ad05e55-2b1a-486c-bc07-ecb3be682d29?key=e42285cfa9a0b157b3f1bdaadcac509c44db4cfa0f90735e12b770acb1307b918cee14d5d8e4d4187eb2cab71fc9233bda8ee3eed924b8a3fad33aaa6c8915fe6f3de6f82ad4b995c2359b168ed88fa9"
	url = testing_url

	print(pd.read_csv(requests.get(url).json()['url']).filter(like='Daily').sum(), file=f)
	print("\n\n", file=f)


# TX
def tx(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	url = 'https://www.dshs.texas.gov/coronavirus/TexasCOVID-19HospitalizationsOverTimebyTSA.xlsx'
	df = pd.read_excel(url, sheet_name='COVID-19 ICU', skiprows=2)
	print("ICU", file=f)
	print(df.loc[df[df.columns[0]] == 'Total'][df.columns[-1]], file=f)

	# PCR Positives
	res = requests.get('https://services5.arcgis.com/ACaLB9ifngzawspq/arcgis/rest/services/TX_DSHS_COVID19_TestData_Service/FeatureServer/6/query?where=1%3D1&outStatistics=%5B%7B%27statisticType%27%3A+%27sum%27%2C+%27onStatisticField%27%3A+%27NewPositive%27%7D%2C+%7B%27statisticType%27%3A+%27sum%27%2C+%27onStatisticField%27%3A+%27OldPositive%27%7D%5D&f=json')
	print("\nPCR Positives", file=f)
	print(sum(res.json()['features'][0]['attributes'].values()), file=f)

	res = requests.get('https://services5.arcgis.com/ACaLB9ifngzawspq/ArcGIS/rest/services/TX_DSHS_COVID19_Cases_Service/FeatureServer/2/query?where=1%3D1&outFields=%2A&orderByFields=Date+desc&resultRecordCount=1&f=json')
	print("\nCases Timestamp (as-of)", file=f)
	cases_date = datetime.fromtimestamp(res.json()['features'][0]['attributes']['Date']/1000)
	# convent to TX time through trickery (from UTC)
	print(cases_date - timedelta(hours=6), file=f)

	# Antigen Positives
	res = requests.get('https://services5.arcgis.com/ACaLB9ifngzawspq/ArcGIS/rest/services/TX_DSHS_COVID19_TestData_Service/FeatureServer/3/query?where=1%3D1&objectIds=&time=&resultType=none&outFields=*&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&sqlFormat=none&f=json')
	print("\nAntigen Positives", file=f)
	print(res.json()['features'][5]['attributes']['Count_'], file=f)

	# Antibody Positives
	print("\nAntibody Positives", file=f)
	print(res.json()['features'][2]['attributes']['Count_'], file=f)
	print("\n\n", file=f)


# UT
def ut(f):
    print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
    url = 'https://coronavirus-dashboard.utah.gov/Utah_COVID19_data.zip'
    res = requests.get(url)
    zipdata = BytesIO(res.content)
    zip = zipfile.ZipFile(zipdata, 'r')
    for zf in zip.filelist:
      if zf.filename.startswith('Overview_Total Tests by Date'):
        # yay, the testing file
        title = 'Tests'
      elif zf.filename.startswith('Overview_Number of People Tested by Date'):
        title = 'People'
      else:
        title = None
      if title:
        title = "Metrics for {} (from {})".format(title, zf.filename)
        print(title, "\n"+"="*len(title), file=f)
        df = pd.read_csv(zip.open(zf.filename)).drop(columns=[' Total Daily Tests', 'Total Positive Tests', 'Daily People Tested', 'Daily Positive Tests'], errors="ignore")
        print(df.groupby(['Test Type', 'Result']).sum(), file=f)
        print("\n\n", file=f)


# WA
def wa(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	wa_link = 'https://www.doh.wa.gov/Portals/1/Documents/1600/coronavirus/data-tables/PUBLIC_Tests_by_Specimen_Collection.xlsx'
	print("Link = ", wa_link, file=f)

	wa = pd.read_excel(wa_link, sheet_name = 'State').filter(regex='(Positive|Negative)').drop(columns='Positive tests (%)')
	wa.columns = [x.split()[0] for x in wa.columns]
	print(wa.groupby(wa.columns.values, axis=1).sum().sum(), file=f)
	print("\n\n", file=f)


# WI PCR Testing Encounters
def wi(f):
	print("Run at: ", datetime.now(tz('US/Eastern')), "\n", file=f)
	wi = pd.read_csv("https://bi.wisconsin.gov/t/DHS/views/PercentPositivebyTestPersonandaComparisonandTestCapacity/TestCapacityDashboard.csv", thousands=",")
	print("PCR Testing Encounters: " + str(wi[wi['Measure Names'] == 'Total people tested daily']['Number of Tests'].sum()), file=f)
	print("\n\n", file=f)


# WV Testing
def wv(f): 
    print("Run at: ", datetime.now(tz('US/Eastern')).isoformat(), "\n", file=f)
    wv = pd.read_csv("https://raw.githubusercontent.com/COVID19Tracking/covid19-datafetcher/data/wv_lab_tests.csv", thousands=",")
    print(wv.loc[:, wv.columns != 'date'].sum(axis=0), file=f)
    print("\n\n", file=f)


def main():
	state = ['de','hi','ma','me', 'mi', 'nc', 'nd', 'oh', 'tx', 'ut', 'wa', 'wi', 'wv']
	for s in state:
		path = '../data/' + s + '.txt'
		fun = globals()[s]
		with open(path, 'a+') as f:
			try:
				fun(f)
			except:
				print("Encountered an error running at", datetime.now(tz('US/Eastern')), file=f)


if __name__ == "__main__":
    main()
