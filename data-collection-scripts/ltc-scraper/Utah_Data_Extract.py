import json
from datetime import datetime
from pytz import timezone
from urllib.request import urlopen

def load_json():
    url = ("https://services6.arcgis.com/KaHXE9OkiB9e63uE/ArcGIS/rest/services/COVID19_Long_Term_Care_Facility_Impacts/FeatureServer/273/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=true&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token=")
    response = urlopen(url)
    if response.getcode() == 200:
        source = response.read()
        dict_data = json.loads(source)
    else:
        print("Error")
    #print(response.read())
    #data = json.loads(response.read())

    #f = open("Facilities_with_Active_Outbreaks.json", "r")
    #data = f.read()
    CSV_file = open("CSV_Data_Extract.csv", "w")

    if not dict_data is None:
        features_list = dict_data["features"]
        for item in features_list:
            fmt = datetime.today().strftime('%Y%m%d')
            now_time = datetime.now(timezone('US/Eastern'))
            line_data = now_time.strftime(fmt)
            line_data += "," + "UT"
            line_data += "," + "" + "," + ""
            line_data += "," + item["attributes"]["Facility_Name"]
            line_data += "," + item["attributes"]["Facility_Type"]
            line_data += "," + "" + "," + "" + "," + "" + "," + "" + "," + "" + "," + ""
            line_data += "," + item["attributes"]["Resolved_Y_N"]
            line_data += "," + ""
            if item["attributes"]["Postive_Patients_Desc"] == "No Resident Cases":
                line_data += "," + "0"
            else:
                line_data += "," + item["attributes"]["Postive_Patients_Desc"]
            line_data += "," + "" + "," + "" + "," + "" + "," + "" + "," + "" + "," + "" + "," + ""
            if item["attributes"]["Resolved_Y_N"] == "N":
                line_data += "," + item["attributes"]["Postive_Patients_Desc"]
            else:
                line_data += "," + ""
            line_data += "," + "" + "," + "" + "," + "" + "," + "" + "," + "" + "," + "" + "," + ""
            line_data += "," + item["attributes"]["Dashboard_Display"]
            CSV_file.write(line_data + "\n")

        CSV_file.close()
