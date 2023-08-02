"""Compare N in papers that report it in the abstract vs papers that report it only in the body."""
import json
import pathlib
import re
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from labelrepo import read_json
from pubextract.participants import annotate_labelbuddy_docs
import utils

# breakpoint()
docs = utils.load_labelbuddy_docs()
annotated_docs = annotate_labelbuddy_docs(docs)
counts = []
annotated_docs = json.loads(
    (utils.get_outputs_dir() / "automatically_annotated_docs.json").read_text(
        "utf-8"
    )
)

for doc_info in annotated_docs:
    annotations = doc_info["annotations"]
    if not annotations:
        continue
    if annotations[0]["label_name"] != "ParticipantsInfo":
        continue
    count = int(
        re.match(
            r"<(\d+) participants:.*", annotations[0]["extra_data"]
        ).group(1)
    )
    abstract_start, abstract_stop = doc_info["metadata"]["field_positions"][
        "abstract"
    ]
    if any(
        (abstract_start <= a["start_char"] and a["end_char"] <= abstract_stop)
        for a in annotations[1:]
    ):
        counts.append({"count": count, "in_abstract": True})
    else:
        counts.append({"count": count, "in_abstract": False})


df = pd.DataFrame(counts)
fig, ax = plt.subplots(figsize=(6, 2))
sns.boxplot(data=df, x="count", y="in_abstract", orient="h", ax=ax)
# sns.stripplot(data=df, x="count", y="in_abstract", orient="h", color="k")
sample_size = df.groupby("in_abstract")["count"].median()
ax.set_ylabel("")
ax.set_xlabel("Sample size (N)")
ax.set_xscale("log")
label_map = {
    "False": f"N not in abstract\n(median = {sample_size[False]:.0f})",
    "True": f"N in abstract\n(median = {sample_size[True]:.0f})",
}
ax.set_yticklabels(
    [label_map[label.get_text()] for label in ax.get_yticklabels()]
)

fig.savefig(
    utils.get_figures_dir() / "n_participants_abstract_vs_body.pdf",
    bbox_inches="tight",
)
