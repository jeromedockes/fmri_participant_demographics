import json

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

MIN_PAPERS = 30
metadata = pd.read_csv(
    "/home/data/no_backup/nqdc_data/query-90f33493e7c1cb24fa7ad33c43bbe27f/subset_articlesWithCoords_extractedData/metadata.csv",
    index_col="pmcid",
)
demographics_file = "/tmp/extracted_data.jsonl"

demographics = []
with open(demographics_file, encoding="utf8") as demo_f:
    for article_json in demo_f:
        article_info = json.loads(article_json)
        article_demographics = {}
        for key in ["count", "females_count", "males_count"]:
            article_demographics[key] = article_info["demographics"][key]
        article_demographics["n_groups"] = len(
            article_info["demographics"]["groups"]
        )
        demographics.append(article_demographics)

metadata = pd.concat(
    [metadata, pd.DataFrame(demographics, index=metadata.index)], axis=1
)
metadata = metadata.dropna(subset="count")
# metadata = metadata[metadata["n_groups"] == 1]

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


def plot_subpops(metadata):
    metadata = metadata[
        metadata["Females"].notnull() & metadata["Males"].notnull()
    ]
    assert (metadata["Females"] + metadata["Males"] == metadata["Total"]).all()
    metadata_tall = (
        metadata.loc[:, ["Total", "Females", "Males"]].stack().reset_index()
    )
    metadata_tall.columns = ["pmcid", "count_type", "count"]
    metadata_tall["publication_year"] = (
        metadata["publication_year"].loc[metadata_tall["pmcid"].values].values
    )

    fig, ax = plt.subplots()
    # for percentile in (25, 50, 75):
    percentile = 50
    sns.lineplot(
        data=metadata_tall,
        x="publication_year",
        y="count",
        style="count_type",
        hue="count_type",
        # ci=None,
        n_boot=1000,
        color="k",
        estimator=lambda x: np.percentile(x, percentile),
        ax=ax,
    )

    # sns.scatterplot(data=metadata, x="publication_year", y="count", ax=ax)
    # ax.set_yscale("log")
    # ax.legend(["total", "", "males", "", "females"])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels, loc="upper left")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Median participant count")
    fig.savefig("/tmp/fig_subpops.png")


def plot_total(metadata):
    fig, ax = plt.subplots()
    # for percentile in (25, 50, 75):
    percentile = 50
    sns.lineplot(
        data=metadata,
        x="publication_year",
        y="Total",
        # ci=None,
        n_boot=1000,
        color="k",
        estimator=lambda x: np.percentile(x, percentile),
        ax=ax,
    )

    # sns.scatterplot(data=metadata, x="publication_year", y="count", ax=ax)
    # ax.set_yscale("log")
    # ax.legend(["total", "", "males", "", "females"])
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Median participant count")
    fig.savefig("/tmp/fig_total.png")


plot_total(metadata)
plot_subpops(metadata)
