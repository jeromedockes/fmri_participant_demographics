"""Extract number of participants from several sources and store in csv.

Get sample size from
- manual annotations
- Poldrack & al extractor
- `participants_demographics` extractor.
"""
import pandas as pd

import participants_demographics
import scanning_horizon
import utils


annotations = utils.load_annotations("jerome_n_participants.json")
all_docs = utils.load_docs()
annotated_n = pd.Series(
    utils.n_participants_from_annotations(annotations, all_docs)
).dropna()

samples = pd.DataFrame({"annotations": annotated_n})
samples.index.name = "pmcid"

for extractor in (participants_demographics, scanning_horizon):
    print(extractor.__name__)
    extracted_n = pd.Series(
        extractor.n_participants_from_labelbuddy_docs(
            [all_docs[pmcid] for pmcid in annotated_n.index]
        ),
        index=annotated_n.index,
    )
    samples[extractor.__name__] = extracted_n

results_dir = utils.get_results_dir("n_participants")
samples.to_csv(results_dir.joinpath("n_participants.csv"))
