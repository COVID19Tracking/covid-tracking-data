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
    # if only one row, return the row
    if df_group.shape[0] == 1:
        return df_group

    new_df_subset = df_group.loc[df_group['Outbreak Status'] == 'Open'].copy()
    if new_df_subset.empty:  # no open outbreaks, but we may want to merge some closed ones
        new_df_subset = df_group.head(1).copy()

    # expecting only one row/open outbreak; if this isn't true, return the group as is
    if new_df_subset.shape[0] > 1:
        print('Check for duplicates: %s %s' % (
            set(new_df_subset['Facility Name']), set(new_df_subset['Date Collected'])))
        return df_group

    for colname in col_map.keys():
        try:
            cumulative_val = int(df_group[colname].astype(float).sum())
            current_open_val = int(df_group[col_map[colname]].astype(float).sum())
            val = cumulative_val + current_open_val
            if val > 0:
                index = list(df_group.columns).index(colname)
                new_df_subset.iat[0,index] = val
        except ValueError:  # some date fields in numeric places, return group without collapsing
            return df_group
    return new_df_subset


def process_df(df):
    num_numeric_cols = 12  # number of metrics
    first_metric_col = 14  # position of 1st metric, "Cumulative Resident Positives"
    col_map = {}
    for i in range(num_numeric_cols):
        cumulative_col = df.columns[first_metric_col+i]
        outbreak_col = df.columns[first_metric_col+i+num_numeric_cols]
        col_map[cumulative_col] = outbreak_col

    # group by facility name and date, collapse each group into one row
    processed_df = df.groupby(
        ['Date Collected', 'Facility Name']).apply(
            lambda x: collapse_rows(x, col_map))
    return processed_df


def lambda_handler(event, context):
    df = pd.read_csv(io.StringIO(event['body']))
    processed_df = process_df(df)
    
    return {
        'statusCode': 200,
        'body': processed_df.to_csv(index=False, header=False)  # don't return the header row
    }
