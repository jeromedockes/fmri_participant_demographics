import json
import argparse

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

import utils

MIN_PAPERS = 30


def plot_subpops(metadata, plots_dir):
    metadata = metadata[metadata["Females"].notnull()]
    assert (metadata["Females"] + metadata["Males"] == metadata["Total"]).all()
    metadata_tall = (
        metadata.loc[:, ["Total", "Females", "Males"]].stack().reset_index()
    )
    metadata_tall.columns = ["pmcid", "count_type", "count"]
    metadata_tall["publication_year"] = (
        metadata["publication_year"].loc[metadata_tall["pmcid"].values].values
    )
    fig, ax = plt.subplots()
    percentile = 50
    sns.lineplot(
        data=metadata_tall,
        x="publication_year",
        y="count",
        style="count_type",
        hue="count_type",
        color="k",
        estimator=lambda x: np.percentile(x, percentile),
        ax=ax,
    )
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels, loc="upper left")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Median participant count")
    fig.savefig(
        plots_dir.joinpath("n_participants_detail.pdf"), bbox_inches="tight"
    )


def plot_total(metadata, plots_dir):
    fig, ax = plt.subplots()
    percentile = 50
    sns.lineplot(
        data=metadata,
        x="publication_year",
        y="Total",
        color="k",
        estimator=lambda x: np.percentile(x, percentile),
        ax=ax,
    )
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Median participant count")
    fig.savefig(
        plots_dir.joinpath("n_participants_total.pdf"), bbox_inches="tight"
    )


parser = argparse.ArgumentParser()
parser.add_argument("articles_metadata_csv")
args = parser.parse_args()

metadata = pd.read_csv(args.articles_metadata_csv, index_col="pmcid")

demographics = []
with open(utils.get_demographics_file(), encoding="utf8") as demo_f:
    for article_json in demo_f:
        article_info = json.loads(article_json)
        article_demographics = {}
        for key in ["count", "females_count", "males_count"]:
            article_demographics[key] = article_info["demographics"][key]
        demographics.append(article_demographics)

metadata = pd.concat(
    [metadata, pd.DataFrame(demographics, index=metadata.index)], axis=1
)
metadata = metadata.dropna(subset="count")

year_counts = (
    metadata["publication_year"].groupby(metadata["publication_year"]).count()
)
good_years = year_counts[year_counts > MIN_PAPERS].index
metadata = metadata[
    (metadata["publication_year"] >= good_years.values.min())
    & (metadata["publication_year"] <= good_years.values.max())
]
metadata["publication_year"] = pd.to_datetime(
    pd.DataFrame({"year": metadata["publication_year"], "month": 1, "day": 1})
)
print("Median N participants:")
print(metadata["count"].groupby(metadata["publication_year"]).median())
print("\nN papers:")
print(metadata["count"].groupby(metadata["publication_year"]).count())
print(metadata.shape)

metadata.rename(
    columns={
        "count": "Total",
        "females_count": "Females",
        "males_count": "Males",
    },
    inplace=True,
)

plots_dir = utils.get_results_dir("participants_demographics_data", "plots")
plot_total(metadata, plots_dir)
plot_subpops(metadata, plots_dir)
