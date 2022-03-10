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
        breakpoint()
        doc["utf8_text_md5_checksum"] = doc["meta"]["text_md5"]
        doc["labels"] = _participants_to_labels(extracted)
        del doc["short_title"]
        del doc["long_title"]
        del doc["text"]
        yield doc
    print()


def _participants_to_labels(participants_info):
    labels = []
    if participants_info.count is not None:
        labels.append(
            (
                0,
                1,
                participants_info.__class__.__name__,
                str(participants_info),
            )
        )
    for group in participants_info.groups:
        labels.extend(_labels_from_group(group))
    _extend_labels(
        participants_info.discarded_group_mentions, "_Discarded", labels
    )
    return labels


def _labels_from_group(group):
    labels = []
    anchor = group.mentions[0]
    labels.append(
        (
            anchor.abs_start_pos,
            anchor.abs_end_pos,
            group.__class__.__name__,
            str(group),
        )
    )
    _extend_labels(anchor.details, None, labels)
    _extend_labels(group.mentions[1:], "_Mention", labels)
    return labels


def _extend_labels(nodes_to_add, kind, labels):
    for node in nodes_to_add:
        labels.append(
            (
                node.abs_start_pos,
                node.abs_end_pos,
                node.__class__.__name__ if kind is None else kind,
                str(node),
            )
        )
        if hasattr(node, "details"):
            _extend_labels(
                node.details,
                kind,
                labels,
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
