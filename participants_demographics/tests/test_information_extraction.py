from pathlib import Path
import json

import pandas as pd
import pytest

from participants_demographics import _information_extraction


@pytest.fixture
def example_text():
    return (
        Path(__file__)
        .parent.joinpath("data", "example_doc.txt")
        .read_text("utf-8")
    )


def test_extractor(example_text):
    extracted = _information_extraction.Extractor().extract(example_text)
    assert extracted.count == 20
    assert extracted.groups[0].name == "patients"
    assert extracted.groups[0].females_count == 5


def test_n_participants_from_texts(example_text):
    texts = [
        example_text,
        "# abstract\n20 participants or 45 subjects",
        example_text,
    ]
    extracted_n = _information_extraction.n_participants_from_texts(texts)
    assert extracted_n == [20, None, 20]


def test_annotate_labelbuddy_docs(example_text):
    doc1 = {
        "text": example_text,
        "metadata": {"text_md5": "doc1md5"},
        "display_title": "",
        "list_title": "",
    }
    doc2 = {
        "text": "no n participants",
        "metadata": {"text_md5": "doc2md5"},
        "display_title": "",
        "list_title": "",
    }
    all_docs = [doc1, doc2]
    annotated = list(
        _information_extraction.annotate_labelbuddy_docs(all_docs)
    )
    assert len(annotated) == 2
    assert annotated[0]["annotations"][0]["extra_data"].startswith(
        "<20 participants"
    )
    extracted_n = _information_extraction.n_participants_from_labelbuddy_docs(
        all_docs
    )
    assert extracted_n == [20, None]


def test_extract_from_dataset(tmp_path, example_text):
    docs = [
        {"pmcid": 0, "title": "fmri", "body": example_text},
        {"pmcid": 1, "body": "some text"},
    ]
    csv_file = tmp_path.joinpath("text.csv")
    pd.DataFrame(docs).to_csv(csv_file, index=False)
    output_file = tmp_path.joinpath("demographics.jsonl")
    _information_extraction.extract_from_dataset(csv_file, output_file)
    extracted = [
        json.loads(doc)
        for doc in output_file.read_text("utf-8").strip().split("\n")
    ]
    assert len(extracted) == 2
    assert extracted[0]["demographics"]["count"] == 20
