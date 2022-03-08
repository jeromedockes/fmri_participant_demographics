from pathlib import Path
import json

from participants import load_docs
from participants._horizon.get_ns_sample_sizes import estimate_n


result = []
all_docs = load_docs()[:100]
for i, doc in enumerate(all_docs):
    print(f"{i + 1} / {len(all_docs)}", end="\r")
    abs_start, abs_end = doc["meta"]["field_positions"]["abstract"]
    abstract = doc["text"][abs_start:abs_end]
    groups = estimate_n(abstract)
    all_labels = []
    total_n = 0
    for snippet, n, start, end in groups:
        total_n += n
        all_labels.append(
            (
                abs_start + start,
                abs_start + end,
                "ParticipantsGroup",
                f"n = {n}",
            )
        )
    doc["labels"] = all_labels
    if doc["labels"]:
        doc["labels"].append(
            (0, 1, "ParticipantsInfo", f"{total_n} participants")
        )
    result.append(doc)

print()
Path("/tmp/horizon_annotations.json").write_text(json.dumps(result), "utf-8")
