import pandas as pd
import os
from publang.pipelines import extract_gpt_demographics
from labelrepo.projects.participant_demographics import get_participant_demographics
from labelrepo.database import get_database_connection

import utils

api_key = os.environ.get('OPENAI_API_KEY', None)
MAX_TOKENS=4000

### Training documents
# Load original annotations
subgroups = get_participant_demographics()
jerome_pd = subgroups[(subgroups.project_name == 'participant_demographics') & \
                      (subgroups.annotator_name == 'Jerome_Dockes')]
subset_cols = ['count', 'diagnosis', 'group_name', 'subgroup_name', 'male count',
       'female count', 'age mean', 'age minimum', 'age maximum',
       'age median', 'pmcid']
jerome_pd_subset = jerome_pd[subset_cols].sort_values('pmcid')

# Load articles
training_docs = pd.read_sql(
    "select pmcid, text from document",
    get_database_connection(),
)
training_docs = training_docs[training_docs.pmcid.isin(jerome_pd.pmcid)].to_dict(orient='records')


training_predictions_path = utils.get_outputs_dir() / f'training_participant_demographics_gpt_tokens-{MAX_TOKENS}.csv'
training_embeddings_path = utils.get_outputs_dir() / f'training_embeddings_tokens-{MAX_TOKENS}.csv'

# Try to open each, if not set to None
training_embeddings, training_predictions = None, None
if os.path.exists(training_embeddings_path):
    training_embeddings = pd.read_csv(training_embeddings_path)
if os.path.exists(training_predictions_path):
    training_predictions = pd.read_csv(training_predictions_path)

if training_predictions is None:
    # Extract
    training_predictions, training_embeddings = extract_gpt_demographics(
        articles=training_docs, embeddings=training_embeddings, api_key=api_key, max_tokens=MAX_TOKENS, num_workers=10
    )
    # Save predictions
    training_predictions.to_csv(training_predictions_path, index=False)
    training_embeddings.to_csv(training_embeddings_path, index=False)

### Evaluation
# Load and extract from evaluation texts
docs = pd.read_csv(utils.get_outputs_dir() / 'evaluation_texts.csv')

predictions_path = utils.get_outputs_dir() / f'participant_demographics_gpt_tokens-{MAX_TOKENS}.csv'
embeddings_path = utils.get_outputs_dir() / f'evaluation_embeddings_tokens-{MAX_TOKENS}.csv'

# Try to open each, if not set to None
embeddings, predictions = None, None
if os.path.exists(embeddings_path):
    embeddings = pd.read_csv(embeddings_path)
if os.path.exists(predictions_path):
    predictions = pd.read_csv(predictions_path)

if predictions is None:
    # Extract
    predictions, embeddings = extract_gpt_demographics(
        articles=docs.to_dict(orient='records'), embeddings=embeddings, api_key=api_key, max_tokens=MAX_TOKENS, num_workers=8
    )
    # Save predictions
    predictions.to_csv(predictions_path, index=False)
    embeddings.to_csv(embeddings_path, index=False)
