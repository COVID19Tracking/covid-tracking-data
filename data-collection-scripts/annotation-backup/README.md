# annotation-backup

Backup data from CTP Airtable

This script is intended to be run as GitHub Actions jobs, with the resulting CSV file ending up in `/data`

Usage:
```shell script
npm install
export AIRTABLE_API_KEY = secret
node annotation_backup.js
```
