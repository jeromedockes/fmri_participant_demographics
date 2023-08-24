#! /usr/bin/env python3

import argparse
import datetime
import json
import pathlib
import sys

from labelrepo import database, repo

parser = argparse.ArgumentParser()
parser.add_argument(
    "-o",
    "--output_file",
    help="JSON file where to write the output. If not provided, a file will "
    "be created in the current working directory. If '-', results are written "
    "to output.",
    type=str,
    default=None,
)

args = parser.parse_args()

stdout = sys.stdout
sys.stdout = sys.stderr

now = datetime.datetime.now().isoformat()

if not repo.git_working_directory_is_clean():
    print(
        "labelbuddy-annotations has uncommitted changes. "
        "There may be some annotations not tracked by Git. "
        "Make sure the working directory is clean before running this script."
    )
    sys.exit(1)

result = {
    "date": now,
    "commit": repo.git_head_checksum(),
}

database.make_database()
connection = database.get_database_connection()
cursor = connection.execute(
    "select distinct pmcid from detailed_annotation "
    "where project_name='participant_demographics'"
)
pmcids = [row["pmcid"] for row in cursor]

result["annotated_pmcids"] = pmcids

if args.output_file == "-":
    stdout.write(json.dumps(result, indent=2))
    stdout.write("\n")
    sys.exit(0)

if args.output_file is None:
    output_file = pathlib.Path.cwd() / f"all_annotated_pmcids_on_{now}.json"
else:
    output_file = pathlib.Path(args.output_file)

output_file.write_text(json.dumps(result), "UTF-8")
