import pandas as pd
import os
from publang.pipelines import extract_gpt_demographics

import utils

api_key = os.environ.get('OPENAI_API_KEY', None)

# Load evaluation texts
docs = pd.read_csv(utils.get_outputs_dir() / 'evaluation_texts.csv')

max_tokens = 2000 # Value chosen after trying a few different values
predictions_path = utils.get_outputs_dir() / f'participant_demographics_gpt_tokens-{max_tokens}.csv'
embeddings_path = utils.get_outputs_dir() / f'evaluation_embeddings_tokens-{max_tokens}.csv'

# Try to open each, if not set to None
embeddings, predictions = None, None
if os.path.exists(embeddings_path):
    embeddings = pd.read_csv(embeddings_path)
if os.path.exists(predictions_path):
    predictions = pd.read_csv(predictions_path)

if predictions is None:
    # Extract
    predictions, embeddings = extract_gpt_demographics(
        articles=docs.to_dict(orient='records'), embeddings=embeddings, api_key=api_key, max_tokens=max_tokens, num_workers=8
    )
    # Save predictions
    predictions.to_csv(predictions_path, index=False)
    embeddings.to_csv(embeddings_path, index=False)
