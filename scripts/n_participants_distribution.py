"""Plot distribution of number of participants for years 2020-2022
"""
import datetime

import seaborn as sns
from matplotlib import pyplot as plt

import utils

MIN_PAPERS = 30
PUBGET_NAME = "pubget [in 2022]"


demographics_data = utils.load_n_participants(MIN_PAPERS).loc[
    :, ["publication_year", "count", "n_groups"]
]
# restrict to single-group studies
demographics_data = demographics_data[demographics_data["n_groups"] == 1]
demographics_data = demographics_data[
    demographics_data["publication_year"]
    > datetime.datetime(year=2017, month=1, day=1)
]
demographics_data["publication_year"] = demographics_data[
    "publication_year"
].dt.year
demographics_data["Data source"] = PUBGET_NAME
print(demographics_data.head())
print(demographics_data.dtypes)

fig, ax = plt.subplots(figsize=(8, 6))
years = demographics_data["publication_year"].unique()
years = years[years.argsort()]

sns.stripplot(
    data=demographics_data,
    x="count",
    y="publication_year",
    orient="h",
    order=years,
    color="k",
    alpha=0.2,
)
ax.set_xscale("log")
sns.despine()


output_file = utils.get_figures_dir() / "n_participants_distribution.pdf"
fig.savefig(output_file, bbox_inches="tight")
