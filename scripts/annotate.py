import json

import participants_demographics

import utils

all_docs = utils.load_docs()
annotations = participants_demographics.annotate_labelbuddy_docs(
    all_docs.values()
)

results_dir = utils.get_results_dir("participants_demographics_annotations")
results_dir.joinpath("annotations.json").write_text(
    json.dumps(list(annotations)), "utf-8"
)
