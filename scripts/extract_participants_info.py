from pathlib import Path
import json

from participants import Extractor, load_docs, summarize

extractor = Extractor()


def participants_to_labels(participants_info):
    labels = []
    if participants_info is None:
        return labels
    labels.append(
        (0, 1, participants_info.__class__.__name__, str(participants_info))
    )
    for group in participants_info.groups:
        for mention in group.mentions:
            labels.append(
                (
                    mention.group.abs_start_pos,
                    mention.group.abs_end_pos,
                    mention.group.__class__.__name__,
                    str(mention.group),
                )
            )
            for detail in mention.group_details:
                labels.append(
                    (
                        detail.abs_start_pos,
                        detail.abs_end_pos,
                        detail.__class__.__name__,
                        str(detail),
                    )
                )
    return labels


result = []
all_docs = load_docs()[:100]
for i, doc in enumerate(all_docs):
    print(f"{i + 1} / {len(all_docs)}", end="\r")
    extracted = summarize(extractor.extract_from_text(doc["text"]))
    # del doc["text"]
    all_labels = participants_to_labels(extracted)
    doc["labels"] = all_labels
    result.append(doc)

print()
Path("/tmp/annotations.json").write_text(json.dumps(result), "utf-8")
