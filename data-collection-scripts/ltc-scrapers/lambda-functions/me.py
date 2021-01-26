"""
This is the content of the lambda function that aggregates cumulative and outbreak data for
a set of states (e.g. ME) that otherwise have multiple rows per date/facility, in a case of
several outbreaks.
"""

import io
import json

import pandas as pd


def make_matching_column_name_map(df):
    # make a map of corresponding column names (cumulative to current)
    num_numeric_cols = 12  # number of metrics
    first_metric_col = 14  # position of 1st metric, "Cumulative Resident Positives"
    col_map = {}
    for i in range(num_numeric_cols):
        cumulative_col = df.columns[first_metric_col+i]
        outbreak_col = df.columns[first_metric_col+i+num_numeric_cols]
        col_map[cumulative_col] = outbreak_col
    return col_map


# takes a dataframe containing the same facility name/date data and collapses the rows.
# Finds conceptually paired columns based on the content of col_map.
def collapse_rows(df_group, col_map):
    new_df_subset = df_group.loc[df_group['Outbreak Status'] == 'Open'].copy()
    if new_df_subset.empty:  # no open outbreaks
        new_df_subset = df_group.head(1).copy()
    assert new_df_subset.shape[0] == 1  # expecting only one row/open outbreak
    for colname in col_map.keys():
        try:
            cumulative_val = int(df_group[colname].astype(float).sum())
            current_open_val = int(df_group[col_map[colname]].astype(float).sum())
            val = cumulative_val + current_open_val
            if val > 0:
                index = list(df_group.columns).index(colname)
                new_df_subset.iat[0,index] = val
        except ValueError:  # some date fields in numeric places, return group as is without collapsing
            return df_group
    return new_df_subset


def lambda_handler(event, context):
    me_df = pd.read_csv(io.StringIO(event['body']))
    num_numeric_cols = 12  # number of metrics
    first_metric_col = 14  # position of 1st metric, "Cumulative Resident Positives"
    col_map = {}
    for i in range(num_numeric_cols):
        cumulative_col = me_df.columns[first_metric_col+i]
        outbreak_col = me_df.columns[first_metric_col+i+num_numeric_cols]
        col_map[cumulative_col] = outbreak_col

    # group by facility name and date, collapse each group into one row
    processed_df = me_df.groupby(
        ['Date Collected', 'Facility Name']).apply(
            lambda x: collapse_rows(x, col_map))
    
    return {
        'statusCode': 200,
        'body': processed_df.to_csv(index=False, header=False)  # don't return the header row
    }
