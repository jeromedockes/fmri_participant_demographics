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
