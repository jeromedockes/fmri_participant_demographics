"""Extract number of participants from several sources/methods and store in csv.

Get sample size from
- manual annotations
- Poldrack & al extractor
- `participants_demographics` extractor.
"""
import pandas as pd

from labelrepo import database, read_json, repo
from labelrepo.projects.participant_demographics import (
    get_participant_demographics,
)
from pubextract import participants

import scanning_horizon
import utils

# database.make_database()

docs = read_json(
    repo.repo_root()
    / "projects"
    / "participant_demographics"
    / "documents"
    / "01_documents_00001.jsonl"
)

pmcids = [d["metadata"]["pmcid"] for d in docs]
participant_groups = get_participant_demographics()
participant_groups = participant_groups[
    participant_groups["project_name"] == "participant_demographics"
]
participant_groups = participant_groups[
    participant_groups["annotator_name"] == "Jerome_Dockes"
]
all_annotated_pmcids = set(participant_groups["pmcid"].values)
docs = [d for d in docs if d["metadata"]["pmcid"] in all_annotated_pmcids]
pmcids = [d["metadata"]["pmcid"] for d in docs]
# participant_groups = participant_groups[
#     participant_groups["pmcid"].isin(pmcids)
# ]

annotations = participant_groups.groupby("pmcid")["count"].sum().reindex(pmcids)

samples = pd.DataFrame({"annotations": annotations})

## For scanning participants give it the abstract
for extractor in (participants, scanning_horizon):
    print(extractor.__name__)
    extracted_n = pd.Series(
        extractor.n_participants_from_labelbuddy_docs(docs),
        index=annotations.index,
    )
    samples[extractor.__name__] = extracted_n


# Load extracted data from GPT
predictions_path = utils.get_outputs_dir() / f'eval_participant_demographics_gpt_tokens-2000.csv'
if predictions_path.exists():
    predictions = pd.read_csv(predictions_path)
    predictions = predictions[predictions.pmcid.isin(pmcids)][['pmcid', 'count']]
    predictions = predictions.groupby('pmcid').sum()
    predictions = predictions.reindex(pmcids)

    extracted_n = pd.Series(
        predictions['count'],
        index=annotations.index,
    )
    samples['gpt'] = extracted_n


samples.to_csv(utils.get_outputs_dir() / "n_participants.csv")
