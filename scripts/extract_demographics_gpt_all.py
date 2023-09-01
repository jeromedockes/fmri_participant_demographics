import utils
import json
import os
import pandas as pd
from publang.pipelines import extract_gpt_demographics, clean_gpt_demo_predictions

with open(utils.get_repo_data_dir() / 'fmri_documents.jsonl', 'r') as f:
    docs = [json.loads(line) for line in f]

MAX_TOKENS = 4000
api_key = os.environ.get('OPENAI_API_KEY', None)

predictions_path = utils.get_outputs_dir() / f'all_documents_participant_demographics_gpt_tokens-{MAX_TOKENS}.csv'
clean_predictions_path = utils.get_outputs_dir() / f'all_documents_participant_demographics_gpt_tokens-{MAX_TOKENS}_clean.csv',
embeddings_path = utils.get_outputs_dir() / f'all_documents_embeddings_tokens-{MAX_TOKENS}.parquet'

# Extract
predictions = extract_gpt_demographics(
    articles=docs, output_path=predictions_path, api_key=api_key, max_tokens=MAX_TOKENS, num_workers=6,
    embeddings_path=embeddings_path
)

clean_gpt_demo_predictions(predictions).to_csv(index=False)