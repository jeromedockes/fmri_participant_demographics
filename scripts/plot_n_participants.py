import json

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
    for ext in "pdf", "png":
        fig.savefig(
            plots_dir.joinpath(f"n_participants_detail.{ext}"),
            bbox_inches="tight",
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
    for ext in "pdf", "png":
        fig.savefig(
            plots_dir.joinpath(f"n_participants_total.{ext}"),
            bbox_inches="tight",
        )


metadata = utils.load_n_participants(MIN_PAPERS)
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
