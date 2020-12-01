# ltc-scraper
Scrape Nevada long-term care facility data

This script loads the 
[Nevada LTC COVID dashboard](https://app.powerbigov.us/view?r=eyJrIjoiNDMwMDI0YmQtNmUyYS00ZmFjLWI0MGItZDM0OTY1Y2Y0YzNhIiwidCI6ImU0YTM0MGU2LWI4OWUtNGU2OC04ZWFhLTE1NDRkMjcwMzk4MCJ9) 
and extracts the data for assisted living and nursing home facilities, outputting CSV format to STDOUT.

This is intended to be run as a GitHub Actions job, with the resulting data ending up in `/data/ltc_nv.csv`

Usage:
```shell script
npm install
node nv_ltc_scraper.js
```