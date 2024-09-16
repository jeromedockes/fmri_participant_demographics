import json
import pathlib

from matplotlib import cm
import pandas as pd

from labelrepo import datasets


TAB10_COLORS = [cm.tab10(i) for i in range(10)]


def get_pubget_data_dir():
    return (
        datasets.get_project_datasets("participant_demographics")[0]
        / "subset_articlesWithCoords_extractedData"
    )


def get_repo_data_dir():
    return pathlib.Path(__file__).resolve().parents[1] / "data"


def get_figures_dir():
    figures_dir = get_repo_data_dir() / "figures"
    figures_dir.mkdir(exist_ok=True)
    return figures_dir


def get_outputs_dir():
    outputs_dir = get_repo_data_dir() / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir


def get_demographics_file():
    return get_outputs_dir() / "demographics.jsonl"


def load_labelbuddy_docs():
    data_dir = get_pubget_data_dir().parent.joinpath(
        "subset_articlesWithCoords_labelbuddyData"
    )
    all_docs = []
    for docs_file in sorted(data_dir.glob("doc*.jsonl")):
        with open(docs_file, encoding="utf-8") as docs_f:
            for doc_json in docs_f:
                doc = json.loads(doc_json)
                if "meta" in doc:
                    doc["metadata"] = doc["meta"]
                if "short_title" in doc:
                    doc["display_title"] = doc["short_title"]
                if "long_title" in doc:
                    doc["list_title"] = doc["long_title"]
                all_docs.append(doc)
    return all_docs


def load_n_participants(min_papers_per_year: int) -> pd.DataFrame:
    metadata = pd.read_csv(
        get_pubget_data_dir().joinpath("metadata.csv"), index_col="pmcid"
    )

    demographics = []
    with open(get_demographics_file(), encoding="utf8") as demo_f:
        for article_json in demo_f:
            article_info = json.loads(article_json)
            article_demographics = {}
            for key in ["count", "females_count", "males_count"]:
                article_demographics[key] = article_info["demographics"][key]
            article_demographics["n_groups"] = max(
                1, len(article_info["demographics"]["groups"])
            )
            for group in article_info["demographics"]["groups"]:
                article_demographics[
                    f"{group['participant_type'].lower()}_count"
                ] = group["count"]
            demographics.append(article_demographics)

    metadata = pd.concat(
        [metadata, pd.DataFrame(demographics, index=metadata.index)], axis=1
    )
    metadata = metadata.dropna(subset="count")

    year_counts = (
        metadata["publication_year"]
        .groupby(metadata["publication_year"])
        .count()
    )
    good_years = year_counts[year_counts > min_papers_per_year].index
    metadata = metadata[
        (metadata["publication_year"] >= good_years.values.min())
        & (metadata["publication_year"] <= good_years.values.max())
    ]
    metadata["publication_year"] = pd.to_datetime(
        pd.DataFrame(
            {"year": metadata["publication_year"], "month": 1, "day": 1}
        )
    )
    return metadata


def _load_scanning_horizon_sample_sizes(file_name) -> pd.DataFrame:
    data = pd.read_csv(
        get_repo_data_dir().joinpath("annotations", file_name),
        sep=" ",
        header=None,
    )
    data.columns = ("pmid", "publication_year", "count")
    data["publication_year"] = pd.to_datetime(
        pd.DataFrame({"year": data["publication_year"], "month": 1, "day": 1})
    )
    return data


def load_neurosynth_sample_sizes() -> pd.DataFrame:
    return _load_scanning_horizon_sample_sizes("neurosynth_study_data.txt")


def load_david_sample_sizes() -> pd.DataFrame:
    return _load_scanning_horizon_sample_sizes("david_sampsizedata.txt")


def load_gpt_sample_sizes() -> pd.DataFrame:
    filepath = (
        get_outputs_dir()
        / "all_documents_participant_demographics_gpt_tokens-4000_clean.csv"
    )
    data = pd.read_csv(filepath)
    # add the dates
    metadata_path = (
        pathlib.Path(__file__).resolve().parents[1] / "data" / "metadata.csv"
    )
    metadata = pd.read_csv(metadata_path)

    for ind, row in data.iterrows():
        pmcid = row["pmcid"]
        year = metadata[metadata["pmcid"] == pmcid]["publication_year"].values[0]
        data.loc[ind, "publication_year"] = int(year)
        
    data["publication_year"] = pd.to_datetime(
        pd.DataFrame({"year": data["publication_year"], "month": 1, "day": 1})
    )
    return data
