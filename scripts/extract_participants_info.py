from pathlib import Path
import json

from participants import Extractor, load_docs

extractor = Extractor()


def participants_to_labels(detailed_participant_group):
    labels = []
    group = detailed_participant_group.group
    labels.append(
        (
            group.abs_start_pos,
            group.abs_end_pos,
            group.__class__.__name__,
            str(group),
        )
    )
    for detail in detailed_participant_group.group_details:
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
    extracted = extractor.extract_from_text(doc["text"])
    # del doc["text"]
    all_labels = []
    for participant_group in extracted:
        all_labels.extend(participants_to_labels(participant_group))
    doc["labels"] = all_labels
    result.append(doc)

print()
Path("/tmp/annotations.json").write_text(json.dumps(result), "utf-8")
