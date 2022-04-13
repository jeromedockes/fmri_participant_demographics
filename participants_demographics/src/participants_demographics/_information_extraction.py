import json
from pathlib import Path

import pandas as pd

from participants_demographics import _reading, _summarization


class Extractor:
    def __init__(self):
        self._reader = _reading.Reader()

    def extract(self, text):
        return _summarization.summarize(self._reader.extract_from_text(text))


def n_participants_from_labelbuddy_docs(documents):
    return n_participants_from_texts(doc["text"] for doc in documents)


def n_participants_from_texts(article_texts):
    extractor = Extractor()
    result = []
    for text in article_texts:
        extracted = extractor.extract(text)
        result.append(extracted.count)
    return result


def annotate_labelbuddy_docs(documents):
    extractor = Extractor()
    for i, doc in enumerate(documents):
        print(f"annotating doc {i}", end="\r", flush=True)
        doc = doc.copy()
        extracted = extractor.extract(doc["text"])
        doc["utf8_text_md5_checksum"] = doc["metadata"]["text_md5"]
        doc["annotations"] = _participants_to_annotations(extracted)
        del doc["display_title"]
        del doc["list_title"]
        del doc["text"]
        yield doc
    print()


def _participants_to_annotations(participants_info):
    annotations = []
    if participants_info.count is not None:
        annotations.append(
            {
                "start_char": 0,
                "end_char": 1,
                "label_name": participants_info.__class__.__name__,
                "extra_data": str(participants_info),
            }
        )
    for group in participants_info.groups:
        annotations.extend(_annotations_from_group(group))
    _extend_annotations(
        participants_info.discarded_group_mentions, "_Discarded", annotations
    )
    return annotations


def _annotations_from_group(group):
    annotations = []
    anchor = group.mentions[0]
    annotations.append(
        {
            "start_char": anchor.abs_start_pos,
            "end_char": anchor.abs_end_pos,
            "label_name": group.__class__.__name__,
            "extra_data": str(group),
        }
    )
    _extend_annotations(anchor.details, None, annotations)
    _extend_annotations(group.mentions[1:], "_Mention", annotations)
    return annotations


def _extend_annotations(nodes_to_add, kind, annotations):
    for node in nodes_to_add:
        annotations.append(
            {
                "start_char": node.abs_start_pos,
                "end_char": node.abs_end_pos,
                "label_name": node.__class__.__name__
                if kind is None
                else kind,
                "extra_data": str(node),
            }
        )
        if hasattr(node, "details"):
            _extend_annotations(
                node.details,
                kind,
                annotations,
            )


def extract_from_dataset(input_file: Path, output_file: Path):
    extractor = Extractor()
    with open(output_file, "w", encoding="utf-8") as output_f:
        with open(input_file, newline="", encoding="utf-8") as input_f:
            all_chunks = pd.read_csv(input_f, chunksize=200, index_col="pmcid")
            i = 0
            for chunk in all_chunks:
                for pmcid, row in chunk.iterrows():
                    i += 1
                    print(f"Reading article {i}", end="\r", flush=True)
                    parts = [f"# {col}\n\n{row[col]}" for col in row.index]
                    text = "\n".join(parts)
                    extracted = extractor.extract(text)
                    output_f.write(
                        json.dumps(
                            {
                                "pmcid": pmcid,
                                "demographics": json.loads(
                                    _summarization.to_json(extracted)
                                ),
                            }
                        )
                    )
                    output_f.write("\n")
            print()
