import os
from pathlib import Path
import json
from collections import defaultdict
from typing import List, Dict, Any


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


def load_docs() -> Dict[int, Dict[str, Any]]:
    all_docs = {}
    docs_file = get_data_dir().joinpath(
        "annotation_inputs", "documents_00001.jsonl"
    )
    with open(docs_file, encoding="utf-8") as docs_f:
        for doc_json in docs_f:
            doc = json.loads(doc_json)
            all_docs[doc["meta"]["pmcid"]] = doc
    return all_docs


def load_annotations(annotations_file_name) -> Dict[int, Dict[str, Any]]:
    all_annotations = {}
    annotations_file = get_data_dir().joinpath(
        "annotations", annotations_file_name
    )
    for doc in json.loads(annotations_file.read_text("utf-8")):
        all_annotations[doc["meta"]["pmcid"]] = doc
    return all_annotations


def n_participants_from_annotations(
    annotations: Dict[int, Dict[str, Any]],
    documents: Dict[int, Dict[str, Any]],
) -> Dict[int, int]:
    annotated_n = {}
    for pmcid, doc in annotations.items():
        all_labels = defaultdict(list)
        for label in doc["labels"]:
            all_labels[label[2]].append(label)
        total_n_labels = (
            all_labels["N included"]
            if "N included" in all_labels
            else all_labels["N participants"]
        )
        if len(total_n_labels) != 1:
            annotated_n[pmcid] = None
        elif len(total_n_labels[0]) == 4:
            annotated_n[pmcid] = int(total_n_labels[0][-1])
        else:
            start, stop, _ = total_n_labels[0]
            text = documents[pmcid]["text"][start:stop]
            annotated_n[pmcid] = int(text)
    return annotated_n
