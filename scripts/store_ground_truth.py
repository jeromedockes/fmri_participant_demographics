#! /usr/bin/env python3

import argparse
import datetime
import json
import pathlib
import sys

import pandas as pd

from labelrepo import database, repo, read_json
from labelrepo.projects.participant_demographics import (
    get_participant_demographics,
)

import utils

parser = argparse.ArgumentParser()
parser.add_argument(
    "-t",
    "--training_pmcids",
    help="JSON file containing the PMCIDs of the training documents, "
    "to be excluded from the evaluation set.",
    type=str,
    default=None,
)
parser.add_argument(
    "-o",
    "--output_dir",
    help="directory where to store the outputs. Default is data/outputs/",
    type=str,
    default=None,
)

args = parser.parse_args()

if not repo.git_working_directory_is_clean():
    print(
        "labelbuddy-annotations has uncommitted changes. "
        "There may be some annotations not tracked by Git. "
        "Make sure the working directory is clean before running this script."
    )
    sys.exit(1)


if args.training_pmcids is None:
    training_pmcids_file = (
        utils.get_repo_data_dir() / "training_pmcids.json"
    ).resolve()
else:
    training_pmcids_file = pathlib.Path(args.training_pmcids)

if args.output_dir is None:
    output_dir = utils.get_outputs_dir()
else:
    output_dir = pathlib.Path(args.output_dir)

training_pmcids_info = json.loads(training_pmcids_file.read_text("UTF-8"))


now = datetime.datetime.now().isoformat()

info = {
    "date": now,
    "commit": repo.git_head_checksum(),
    "training_pmcids": training_pmcids_info,
}

docs_full = read_json(
    repo.repo_root()
    / "projects"
    / "participant_demographics"
    / "documents"
    / "01_documents_00001.jsonl"
)
docs = pd.DataFrame(
    [
        {
            "pmcid": d["metadata"]["pmcid"],
            "text": d["text"],
            "abstract": d["text"][
                d["metadata"]["field_positions"]["abstract"][0] : d[
                    "metadata"
                ]["field_positions"]["abstract"][1]
            ],
        }
        for d in docs_full
    ]
).set_index("pmcid")


database.make_database()
annotations = get_participant_demographics()
pmcids = docs.index.intersection(annotations["pmcid"]).difference(
    training_pmcids_info["annotated_pmcids"]
)

annotations = annotations[
    (annotations["project_name"] == "participant_demographics")
    & (annotations["annotator_name"] == "Jerome_Dockes")
    & (annotations["pmcid"].isin(pmcids))
].sort_values(by="pmcid")
docs = docs.loc[pmcids].sort_values(by="pmcid")
pmcids = docs.index.values

papers = annotations.groupby("pmcid", sort=True)
total_count = papers["count"].sum()
assert (total_count.index == pmcids).all()
average_count = papers["count"].mean()
assert (average_count.index == pmcids).all()
n_groups = papers["count"].count()
assert (n_groups.index == pmcids).all()
annotations_summary = pd.DataFrame(
    {
        "pmcid": docs.index.values,
        "total_count": total_count,
        "average_count": average_count,
        "n_groups": n_groups,
    }
)
annotations_summary.to_csv(
    output_dir / "evaluation_labels_summaries.csv", index=False
)
annotations.to_csv(output_dir / "evaluation_labels.csv", index=False)
docs.to_csv(output_dir / "evaluation_texts.csv", index=True)
(output_dir / "evaluation_set_info.json").write_text(
    json.dumps(info), encoding="UTF-8"
)

print(f"{len(pmcids)} evaluation documents stored.")
