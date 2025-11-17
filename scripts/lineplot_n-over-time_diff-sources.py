"""Plot median number of participants through time from multiple sources.

The plot shows the median for each year from 3 sources:
- David & al annotations distributed in https://github.com/poldracklab/ScanningTheHorizon
- Annotations of NeuroSynth abstracts distributed in https://github.com/poldracklab/ScanningTheHorizon
- Sample sizes automatically extracted from pubget data.
"""
from pathlib import Path

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd

import utils

MIN_PAPERS = 20
NS_NAME = "Poldrack & al. [2017]"
DAVID_NAME = "David & al. [2013]"
PUBGET_NAME = "pubextract heuristic [in 2023]"
GPT_NAME = "GPT-3 [in 2023]"

np.random.seed(0)

demographics_file = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "outputs"
    / "n_participants_full_dataset.csv"
)
demographics_data = pd.read_csv(demographics_file)
# restrict to single-group studies
demographics_data = demographics_data[demographics_data["n_groups"] == 1]
demographics_data = demographics_data.loc[:, ["publication_year", "count"]]
demographics_data["Data source"] = PUBGET_NAME
demographics_data["publication_year"] = pd.to_datetime(
    pd.DataFrame({"year": demographics_data["publication_year"], "month": 1, "day": 1})
)
year_counts = demographics_data["publication_year"].value_counts()
years_with_too_few = year_counts[year_counts < MIN_PAPERS].index.values
demographics_data = demographics_data[~demographics_data["publication_year"].isin(years_with_too_few)]

neurosynth_data = utils.load_neurosynth_sample_sizes().loc[
    :, ["publication_year", "count"]
]
neurosynth_data["Data source"] = NS_NAME

david_data = utils.load_david_sample_sizes().loc[
    :, ["publication_year", "count"]
]
david_data["Data source"] = DAVID_NAME

gpt_data = utils.load_gpt_sample_sizes().loc[
    :, ["publication_year", "count", "pmcid"]
]
# restrict to single-group studies
for pmcid, group in gpt_data.groupby("pmcid"):
    gpt_data.loc[group.index, "n_groups"] = len(group)
gpt_data = gpt_data[gpt_data["n_groups"] == 1]
gpt_data = gpt_data.loc[:, ["publication_year", "count"]]
gpt_data["Data source"] = GPT_NAME
# get rid of years with too few papers
year_counts = gpt_data["publication_year"].value_counts()
years_with_too_few = year_counts[year_counts < MIN_PAPERS].index.values
gpt_data = gpt_data[~gpt_data["publication_year"].isin(years_with_too_few)]

data = pd.concat(
    [
        demographics_data,
        neurosynth_data,
        david_data,
        gpt_data
    ], axis=0, ignore_index=True
)


fig, ax = plt.subplots(figsize=(9, 5))
ax.grid(which='major', axis='y', color='gray', alpha=.3)
percentile = 50
sns.lineplot(
    data=data,
    x="publication_year",
    y="count",
    hue="Data source",
    hue_order=(DAVID_NAME, NS_NAME, PUBGET_NAME, GPT_NAME),
    palette=np.asarray(utils.TAB10_COLORS[:4])[[2, 0, 1, 3]],
    style="Data source",
    estimator=lambda x: np.percentile(x, percentile),
    ax=ax,
)
ax.set_xlabel("Publication year")
ax.set_ylabel("Median sample size")
ax.set_ylim(0, 40)
ax.set_xlim(data["publication_year"].min(), data["publication_year"].max())
# ax.legend(loc="upper left", frameon=False)

sns.move_legend(ax, "upper left")

sns.despine()

output_file = utils.get_figures_dir() / "lineplot_n-over-time_diff-sources.pdf"
fig.savefig(output_file, bbox_inches="tight")
