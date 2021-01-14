import json
from datetime import datetime
from pytz import timezone
from urllib.request import urlopen
import sys
from itertools import repeat
import csv
from io import StringIO

"""Fetch Utah's LTC dashboard data and output the data table to STDOUT"""


def load_json():
    url = (
        "https://services6.arcgis.com/KaHXE9OkiB9e63uE/ArcGIS/rest/services/COVID19_Long_Term_Care_Facility_Impacts/FeatureServer/273/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=true&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token=")
    response = urlopen(url)
    status_code = response.getcode()
    if status_code == 200:
        source = response.read()
        return json.loads(source)
    else:
        print("URL request failed with status code: " + status_code)
        sys.exit(1)


dict_data = load_json()

if dict_data is None:
    print("Facility data was empty")
    sys.exit(1)

# build up a list of the output columns, matching the format of the LTC facility data sheet
fieldnames = ["Date Collected", "State"]
fieldnames.extend(repeat("blank", 2))
fieldnames.extend(["Facility_Name", "Facility_Type"])
fieldnames.extend(repeat("blank", 6))
fieldnames.append("Resolved_Y_N")
fieldnames.append("blank")
fieldnames.append("Postive_Patients_Desc")  # intentional—it's spelled wrong in the source JSON
fieldnames.extend(repeat("blank", 7))
fieldnames.append("Unresolved_Postive_Patients_Desc")
fieldnames.extend(repeat("blank", 7))
fieldnames.append("Dashboard_Display")

# output CSV data
si = StringIO()
writer = csv.DictWriter(si, fieldnames, extrasaction='ignore')
writer.writeheader()

for facility in dict_data["features"]:
    facility = facility["attributes"]

    facility["Date Collected"] = datetime.now(timezone('US/Eastern')).strftime('%Y%m%d')
    facility["State"] = "UT"
    facility["blank"] = ""
    writer.writerow(facility)

print(si.getvalue())
