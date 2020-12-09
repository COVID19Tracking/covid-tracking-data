from datetime import date 
from datetime import timedelta

# NOTE: the %#d (day of month not zero padded) and %#m (number of month not zero padded) formatting directives 
#       are different depending on whether you're running on unix or windows. Unix is %-d, windows is %#d. 
# NOTE: %B (full month name) makes capitalized months, which doesn't match the existing urls. The web server was doing an extra redirect to sort it out, so I did tolower().

# MA PRIMARY
# =CONCATENATE("https://www.mass.gov/doc/covid-19-dashboard-",LOWER(TEXT(now(),"mmmm")),"-",LOWER(TEXT(now(),"d")),"-" , YEAR(NOW()),"/download")
print("https://www.mass.gov/doc/covid-19-dashboard-december-9-2020/download")
print(eval("date.today().strftime(\"https://www.mass.gov/doc/covid-19-dashboard-%B-%#d-%Y/download\").lower()"))

# MA SECONDARY
# =CONCATENATE("https://www.mass.gov/doc/weekly-covid-19-public-health-report-",LOWER(TEXT(now(),"mmmm")),"-",LOWER(TEXT(now(),"d")),"-" , YEAR(NOW()),"/download")
print("https://www.mass.gov/doc/weekly-covid-19-public-health-report-december-9-2020/download")
print(eval("date.today().strftime(\"https://www.mass.gov/doc/weekly-covid-19-public-health-report-%B-%#d-%Y/download\").lower()"))

# MT TERTIARY
# =CONCATENATE("https://dphhs.mt.gov/Portals/85/publichealth/documents/CDEpi/DiseasesAtoZ/2019-nCoV/Status%20Update%20Data%20Report_",MONTH(NOW()),if(DAY(NOW())<10,CONCATENATE(0,DAY(NOW())),DAY(NOW())),"20",TEXT(NOW(),"y"),".pdf")
print("https://dphhs.mt.gov/Portals/85/publichealth/documents/CDEpi/DiseasesAtoZ/2019-nCoV/Status%20Update%20Data%20Report_12092020.pdf")
print(eval("date.today().strftime(\"https://dphhs.mt.gov/Portals/85/publichealth/documents/CDEpi/DiseasesAtoZ/2019-nCoV/Status%%20Update%%20Data%%20Report_%m%d%Y.pdf\")"))

# OK SECONDARY
# =CONCATENATE("https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/eo_-_covid-19_report_-_",MONTH(NOW()-1),"-",DAY(NOW()-1),"-",TEXT(NOW()-1,"y"),".pdf")
print("https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/eo_-_covid-19_report_-_12-8-20.pdf")
print(eval("(date.today() - timedelta(days=1)).strftime(\"https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/eo_-_covid-19_report_-_%#m-%#d-%y.pdf\")"))

# OK TERTIARY
# =CONCATENATE("https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/","2020",".",MONTH(NOW()-1),".",DAY(NOW()-1),"_weekly_epi_report.pdf")
print("https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/2020.12.8_weekly_epi_report.pdf")
print(eval("(date.today() - timedelta(days=1)).strftime(\"https://coronavirus.health.ok.gov/sites/g/files/gmc786/f/%Y.%#m.%#d_weekly_epi_report.pdf\")"))
