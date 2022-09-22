"""Extract n participants for all documents in the fmri[abstract] dataset using
the participants_demographics method.

this is different from extract_n_participants which extracts n participants
only for annotated docs, for participants_demographics, scanning_horizon and
manual annotations method.

"""
import pandas as pd
import participants_demographics

import utils

all_docs = list(utils.load_all_docs())
extracted_n = participants_demographics.n_participants_from_labelbuddy_docs(
    all_docs
)
extracted_n_series = pd.Series(
    extracted_n, index=[doc["metadata"]["pmcid"] for doc in all_docs]
)
extracted_n_series.index.name = "pmcid"
extracted_n_series.name = "n_participants"
extracted_n_series.to_csv(
    utils.get_results_dir("n_participants").joinpath(
        "n_participants_all_docs.csv"
    )
)
