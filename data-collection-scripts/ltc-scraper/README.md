# ltc-scraper

Scrape long-term care facility data from various states

* ```nv_ltc_scraper.js``` This script loads the 
[Nevada LTC COVID dashboard](https://app.powerbigov.us/view?r=eyJrIjoiNDMwMDI0YmQtNmUyYS00ZmFjLWI0MGItZDM0OTY1Y2Y0YzNhIiwidCI6ImU0YTM0MGU2LWI4OWUtNGU2OC04ZWFhLTE1NDRkMjcwMzk4MCJ9) 
and extracts the data for assisted living and nursing home facilities, outputting CSV format to STDOUT.
* ```wv_ltc_scraper.js``` This script extracts the data from the 
[West Virginia LTC COVID Dashboard](https://dhhr.wv.gov/COVID-19/Pages/default.aspx) 
(Long-Term Care tab)

These scripts are intended to be run as a GitHub Actions job, with the resulting CSV files ending up in `/data/` 
(e.g. `data/ltc_nv.csv`)

Usage:
```shell script
npm install
node nv_ltc_scraper.js
```
