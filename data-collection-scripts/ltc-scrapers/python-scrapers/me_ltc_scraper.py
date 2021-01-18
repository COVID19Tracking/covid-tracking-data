"""
Not a raw data scraper: instead, this takes the constructed ME facility sheet and collapses all
rows relating to some facility name and date into one row, preserving outbreak and cumulative
information.
"""

import pandas as pd


me_ltc_sheet = 'https://docs.google.com/spreadsheets/d/1oMJHd7Jub6Qtv-fXKYeMbBZJOGmZOVJIUHVSWfa88X0/gviz/tq?tqx=out:csv&sheet=ME'
me_df = pd.read_csv(me_ltc_sheet)

# make a map of corresponding column names (cumulative to current)
num_numeric_cols = 12  # number of metrics
first_metric_col = 14  # position of 1st metric, "Cumulative Resident Positives"
col_map = {}
for i in range(num_numeric_cols):
    cumulative_col = me_df.columns[first_metric_col+i]
    outbreak_col = me_df.columns[first_metric_col+i+num_numeric_cols]
    col_map[cumulative_col] = outbreak_col

# takes a dataframe containing the same facility name/date data and collapses the rows
def collapse_rows(df_group):
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

# group by facility name and date, collapse each group into one row
processed_df = me_df.groupby(['Facility Information Date Collected', 'Facility Name']).apply(collapse_rows)
print(processed_df.to_csv(index=False))
