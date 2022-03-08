import os
from pathlib import Path
import json
from typing import List, Dict, Any


def get_data_dir() -> Path:
    data_dir = os.environ.get("PARTICIPANTS_DATA_DIR")
    if data_dir is not None:
        return Path(data_dir)
    return Path(__file__).parents[2].joinpath("data")


def load_docs() -> List[Dict[str, Any]]:
    docs_file = get_data_dir().joinpath(
        "annotation_inputs", "documents_00001.jsonl"
    )
    with open(docs_file, encoding="utf-8") as docs_f:
        return [json.loads(doc) for doc in docs_f]
