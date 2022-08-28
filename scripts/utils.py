import os
from pathlib import Path
import json
from collections import defaultdict
from typing import List, Dict, Any

from matplotlib import cm
import pandas as pd


TAB10_COLORS = [cm.tab10(i) for i in range(10)]


def get_data_dir() -> Path:
    data_dir = os.environ.get("PARTICIPANTS_DEMOGRAPHICS_DATA_DIR")
    if data_dir is not None:
        return Path(data_dir)
    return Path(__file__).parents[1].joinpath("data")


def get_results_dir(*dir_names: str) -> Path:
    results_dir = get_data_dir().joinpath("results", *dir_names)
    results_dir.mkdir(exist_ok=True, parents=True)
    return results_dir


def get_demographics_file():
    return get_results_dir("participants_demographics_data").joinpath(
        "demographics.jsonl"
    )


def get_nqdc_data_dir() -> Path:
    data_dir = os.environ.get("PARTICIPANTS_DEMOGRAPHICS_NQDC_DATA_DIR")
    if data_dir is not None:
        return Path(data_dir)
    return get_data_dir().joinpath("nqdc_data")


def load_docs() -> Dict[int, Dict[str, Any]]:
    all_docs = {}
    docs_file = get_data_dir().joinpath(
        "annotation_inputs", "documents_00001.jsonl"
    )
    with open(docs_file, encoding="utf-8") as docs_f:
        for doc_json in docs_f:
            doc = json.loads(doc_json)
            all_docs[doc["metadata"]["pmcid"]] = doc
    return all_docs


def load_annotations(annotations_file_name) -> Dict[int, Dict[str, Any]]:
    all_annotations = {}
    annotations_file = get_data_dir().joinpath(
        "annotations", annotations_file_name
    )
    for doc in json.loads(annotations_file.read_text("utf-8")):
        all_annotations[doc["metadata"]["pmcid"]] = doc
    return all_annotations


def n_participants_from_annotations(
    annotations: Dict[int, Dict[str, Any]],
    documents: Dict[int, Dict[str, Any]],
) -> Dict[int, int]:
    annotated_n = {}
    for pmcid, doc in annotations.items():
        all_annotations = defaultdict(list)
        for annotation in doc["annotations"]:
            all_annotations[annotation["label_name"]].append(annotation)
        total_n_annotations = (
            all_annotations["N included"]
            if "N included" in all_annotations
            else all_annotations["N participants"]
        )
        if len(total_n_annotations) != 1:
            annotated_n[pmcid] = None
        elif "extra_data" in total_n_annotations[0]:
            annotated_n[pmcid] = int(total_n_annotations[0]["extra_data"])
        else:
            start = total_n_annotations[0]["start_char"]
            end = total_n_annotations[0]["end_char"]
            text = documents[pmcid]["text"][start:end]
            annotated_n[pmcid] = int(text)
    return annotated_n


def load_n_participants(min_papers_per_year: int) -> pd.DataFrame:
    metadata = pd.read_csv(
        get_nqdc_data_dir().joinpath("metadata.csv"), index_col="pmcid"
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
        get_data_dir().joinpath("annotations", file_name),
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
