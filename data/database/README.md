# The Covid Tracking Project database files

In this folder are the database schema, table content and descriptions (this file) for the DB used by The Covid Tracking Project.

### Codename: TACO
The main data published by The Covid Tracking Project.

Tables:
- `coreData`
- `batches`
- `states`

created with SQLAlchemy. The schema will be exported, but it can also be created from the schema files that will be available here.
More info about the DB structure and management is in [Covid Publishing API Repo](https://github.com/COVID19Tracking/covid-publishing-api)

We want 3 separate views of TACO data:
  - [Official] Data published by CTP (until data collection stopped, on 7-March, 2021)
  - [Research] Research Data (data post 7-March, 2021)
  - [Complete] Unified view of everything, CTP official data and research data


### Codename: Avocado
- `avocado`: A table that's updated daily, schedule via `cron`
- `local_avocados`: data parsed and stored from state files, downloaded by CTP before the start of Avocado project

Research data collected by The Covid Tracking Project.


## How these files were created
### TACO
Schema Export
```
pg_dump -s -O -x -t '"coreData"' -t batches -t states -f taco_schema.sql
```
If using [covid-publishing-api project](https://github.com/COVID19Tracking/covid-publishing-api), then `alembic` can create the schema for you.

Schema file: taco_schema.sql

##### Exporting TACO Official data
 - CSV
   ```
   psql --csv -Pfooter=off -c "select * from states;" -o states_official.csv
   psql --csv -Pfooter=off -c "select * from batches where \"dataEntryType\" not like 'research%';" -o batches_official.csv
   psql --csv -Pfooter=off -c "select * from \"coreData\" where \"batchId\" in (select \"batchId\" from batches where \"dataEntryType\" not like 'research%');" -o core_data_official.csv
   ```
- Exporting Research data
 - CSV
   ```
   psql --csv -Pfooter=off -c "select * from states;" -o states_research.csv
   psql --csv -Pfooter=off -c "select * from batches where \"dataEntryType\" like 'research%';" -o batches_research.csv
   psql --csv -Pfooter=off -c "select * from \"coreData\" where \"batchId\" in (select \"batchId\" from batches where \"dataEntryType\" like 'research%');" -o core_data_research.csv
   ```

##### Exporting TACO Complete data
 - SQL
   ```
   pg_dump -a -O -x -t states -t '"coreData"' -t batches --inserts -f taco_complete.sql
   ```
 - CSV
   ```
   psql --csv -Pfooter=off -c "select * from states;" -o states_complete.csv
   psql --csv -Pfooter=off -c "select * from batches;" -o batches_complete.csv
   psql --csv -Pfooter=off -c "select * from \"coreData\";" -o core_data_complete.csv
    ```
 

### Avocado
It's all research data, no versions here.

- Schema export
  ```
  pg_dump -s -O -x -t avocado -f avocado_schema.sql
  ```
- Export clean view of avocado
First, need to build a view to arrange everything, then export the view content as CSV/build tables from the view to export with `pg_dump` 
  ```
  CREATE VIEW
  avocado_complete AS (
  WITH
    latest_daily AS (
    SELECT state, fetch_timestamp:: date, MAX(fetch_timestamp) ft
    FROM avocado
    GROUP BY fetch_timestamp::date, state
    ORDER BY fetch_timestamp DESC)
  SELECT
    avocado.state,
    date_used,
    "timestamp"::date,
    avocado.fetch_timestamp::date,
    date,
    positive,
    "positiveCasesViral",
    "probableCases",
    death,
    "deathConfirmed",
    "deathProbable",
    total,
    "totalTestsAntibody",
    "positiveTestsAntibody",
    "negativeTestsAntibody",
    "totalTestsViral",
    "positiveTestsViral",
    "negativeTestsViral",
    "totalTestEncountersViral",
    "totalTestsAntigen",
    "positiveTestsAntigen",
    "negativeTestsAntigen"
  FROM avocado
  JOIN latest_daily d
  ON (avocado.fetch_timestamp = d.ft AND avocado.state = d.state) UNION
  SELECT
    state,
    date_used,
    "timestamp"::date,
    fetch_timestamp::date,
    date,
    positive,
    "positiveCasesViral",
    "probableCases",
    death,
    "deathConfirmed",
    "deathProbable",
    total,
    "totalTestsAntibody",
    "positiveTestsAntibody",
    "negativeTestsAntibody",
    "totalTestsViral",
    "positiveTestsViral",
    "negativeTestsViral",
    "totalTestEncountersViral",
    "totalTestsAntigen",
    "positiveTestsAntigen",
    "negativeTestsAntigen"
  FROM
    local_avocados);
  ```

When the view is ready, we can query it. It doesn't have to be a view, but it's more convenient this way.

- CSV export
```
psql --csv -Pfooter=off -c "select * from avocado_complete;" -o avocado_complete.csv
```


### How to use these files

## Data
