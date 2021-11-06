import json
import git
import csv
import sys
import click
from collections import defaultdict

# we want our columns to come out in the desired order, and older pythons don't guarantee dict ordering
MIN_PYTHON = (3, 7)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


@click.command()
@click.argument('filename')
@click.argument('json_key')
@click.option('--strip-duplicate-days/--no-strip-duplicate-days', default=False,
              help='Process the data to only output one set of data for each day')
def main(filename, json_key, strip_duplicate_days):
    repo = git.Repo("../../")

    # fetch all the git commits that updated the data file
    # thanks to https://stackoverflow.com/q/28803626
    revlist = (
        (commit, (commit.tree / filename).data_stream.read())
        for commit in repo.iter_commits(paths=filename)
    )

    # build up a dict of the data history by looking at each commit in the git history
    data = {}
    for commit, filecontents in revlist:
        try:
            data[commit.committed_datetime] = json.loads(filecontents)
        except ValueError as e:  # ignore invalid files: a corrupt download can get into the git history
            pass

    # go through the data and reformat it into one line per batch/state
    # if --strip-duplicate-days is set, we only keep the latest set of data for any state/date pair
    out_data = []
    out_cols = {"runid": None}
    seen_data = defaultdict(set)  # dict with date keys holding the states we've seen for that date
    for data_time, data_batch in data.items():
        for state_data in data_batch[json_key]:
            state_data["runid"] = data_batch["runid"]

            # there's an anomaly in the data where one day has the date in the wrong format.
            # reformat it, hoping this was a one-time glitch
            if state_data["Date"] == "01/12/2021":
                state_data["Date"] = "2021-01-12"

            # have we seen this state/date before?
            if strip_duplicate_days and state_data["ShortName"] in seen_data[state_data["Date"]]:
                continue

            # keep track of all the columns that exist as we go (we'll need that list for the CSV output)
            for k in state_data.keys():
                out_cols[k] = None
            # and keep track of the state/date pairs we've seen
            seen_data[state_data["Date"]].add(state_data["ShortName"])
            # and append the state's data to our output
            out_data.append(state_data)

    # output the data in CSV format
    writer = csv.DictWriter(sys.stdout, out_cols.keys())
    writer.writeheader()
    writer.writerows(out_data)


if __name__ == "__main__":
    main()
