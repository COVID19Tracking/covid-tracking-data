# cdc-vaccination-timeseries

Crawl through the git history of `data/cdc_vaccinations.json`, transform the archived data into a CSV 
time series, and output it to STDOUT.

Pass the optional `--strip-duplicate-days` flag to output only one set of data for each date, keeping only the latest 
data in the case of duplicates.

This is intended to be run a GitHub Actions job, with the resulting CSV file ending up in `/data/`

Usage:
```shell script
pip install -r requirements.txt
python make_timeseries.py
```
