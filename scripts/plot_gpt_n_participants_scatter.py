"""Evaluate sample size extraction."""
import pprint
import json

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn import neighbors

from matplotlib import pyplot as plt


import utils

# Load evaluation annotations
annotations = pd.read_csv(utils.get_outputs_dir() / 'evaluation_labels.csv')
predictions_gpt = pd.read_csv(utils.get_outputs_dir() / 'eval_participant_demographics_gpt_tokens-2000.csv')

# Sum values for each pmcid

# Sum values for each pmcid
annotations_count_summed = annotations.groupby('pmcid')['count'].sum().reset_index()
predictions_gpt_count_summed = predictions_gpt.groupby('pmcid')['count'].sum().reset_index()


# make scatter plot
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(annotations_count_summed['count'], predictions_gpt_count_summed['count'])

# Add line
x = np.linspace(*ax.get_xlim())
ax.plot(x, x, color='black', linestyle='--')

ax.set_xlabel('Annotations')
ax.set_ylabel('GPT')
ax.set_title('Participant count (summed)')

plt.show()
