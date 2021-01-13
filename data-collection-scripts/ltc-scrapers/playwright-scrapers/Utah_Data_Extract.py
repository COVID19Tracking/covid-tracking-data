import json
from datetime import datetime
from pytz import timezone
from urllib.request import urlopen
import sys
import csv
from io import StringIO

def load_json():
    url = ("https://services6.arcgis.com/KaHXE9OkiB9e63uE/ArcGIS/rest/services/COVID19_Long_Term_Care_Facility_Impacts/FeatureServer/273/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=true&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token=")
    response = urlopen(url)
    status_code = response.getcode()
    if status_code == 200:
        source = response.read()
        dict_data = json.loads(source)
    else:
        print("URL request failed with status code: " + status_code)
        sys.exit(1)

    if not dict_data is None:
        features_list = dict_data["features"]
        si = StringIO()
        fieldnames=["Date Collected", "State", "blank1",
                    "blank2", "Facility_Name", "Facility_Type", "blank3",
                    "blank4", "blank5", "blank6", "blank7", "blank8", "Resolved_Y_N",
                    "blank9", "Postive_Patients_Desc", "blank10", "blank11", "blank12",
                    "blank13", "blank14", "blank15", "blank16",
                    "Unresolved_Postive_Patients_Desc",
                    "blank17", "blank18", "blank19", "blank20",  "blank21", "blank22", "blank23",
                    "Dashboard_Display"]
        writer = csv.DictWriter(si, fieldnames)

        writer.writeheader()

        for item in features_list:
            row_data = '{"Date Collected": '
            row_data += datetime.now(timezone('US/Eastern')).strftime('%Y%m%d')
            row_data += ', "State": "UT", "blank1": "", "blank2": "", "Facility_Name": "'
            row_data += (item["attributes"]["Facility_Name"])

            row_data += '","Facility_Type": "'
            row_data += item["attributes"]["Facility_Type"]

            row_data += '", "blank3":"", "blank4": "", "blank5": "", "blank6": "", "blank7":"", "blank8": ""'
            row_data += ', "Resolved_Y_N": "'
            row_data += item["attributes"]["Resolved_Y_N"]

            row_data += '", "blank9": "", "Postive_Patients_Desc": "'
            if item["attributes"]["Postive_Patients_Desc"] == "No Resident Cases":
                row_data += '0'
            else:
                row_data += item["attributes"]["Postive_Patients_Desc"]

            row_data += '", "blank10":"","blank11":"","blank12":"","blank13":"","blank14":"","blank15":"","blank16": ""'
            row_data += ', "Unresolved_Postive_Patients_Desc": "'
            if item["attributes"]["Resolved_Y_N"] == "N":
                row_data += item["attributes"]["Postive_Patients_Desc"]
            else:
                row_data += ''
            row_data += '", "blank17":"","blank18":"","blank19": "", "blank20":"", "blank21":"", "blank22":"","blank23":""'
            row_data += ', "Dashboard_Display": "'
            row_data += item["attributes"]["Dashboard_Display"]

            row_data += '"}'

            row_dict = json.loads(row_data)
            writer.writerow(row_dict)

        print(si.getvalue())
