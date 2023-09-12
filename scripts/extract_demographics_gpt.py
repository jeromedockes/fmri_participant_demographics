import pandas as pd
import os
from publang.pipelines import extract_gpt_demographics, clean_gpt_demo_predictions
from labelrepo.projects.participant_demographics import get_participant_demographics
from labelrepo import database

import utils

api_key = os.environ.get('OPENAI_API_KEY', None)

### Training documents
# Load original annotations
subgroups = get_participant_demographics()
jerome_pd = subgroups[(subgroups.project_name == 'participant_demographics') & \
                      (subgroups.annotator_name == 'Jerome_Dockes')]
subset_cols = ['count', 'diagnosis', 'group_name', 'subgroup_name', 'male count',
       'female count', 'age mean', 'age minimum', 'age maximum',
       'age median', 'pmcid']
jerome_pd_subset = jerome_pd[subset_cols].sort_values('pmcid')

database.make_database()

# Load articles
docs = pd.read_sql(
    "select pmcid, text from document",
    database.get_database_connection(),
)
docs = docs[docs.pmcid.isin(jerome_pd.pmcid)].to_dict(orient='records')

for n_tokens in [2000, 4000]:

    predictions_path = utils.get_outputs_dir() / f'eval_participant_demographics_gpt_tokens-{n_tokens}.csv'
    clean_predictions_path = utils.get_outputs_dir() / f'eval_participant_demographics_gpt_tokens-{n_tokens}_clean.csv'
    embeddings_path = utils.get_outputs_dir() / f'eval_embeddings_tokens-{n_tokens}.parquet'

    # Extract
    predictions = extract_gpt_demographics(
        articles=docs, output_path=predictions_path, api_key=api_key, max_tokens=n_tokens, num_workers=6,
        embeddings_path=embeddings_path
    )

    clean_gpt_demo_predictions(predictions).to_csv(clean_predictions_path, index=False)