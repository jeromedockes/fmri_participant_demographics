import json

import pandas as pd
from sklearn import metrics
from matplotlib import pyplot as plt

import participants_demographics
import scanning_horizon
import utils


annotations = json.loads(
    utils.get_data_dir()
    .joinpath("annotations", "annotations_jerome.json")
    .read_text("utf-8")
)


all_docs = {doc["meta"]["pmcid"]: doc for doc in utils.load_docs()}

annotated_n = {}
for doc in annotations:
    pmcid = doc["meta"]["pmcid"]
    total_n_labels = [
        label for label in doc["labels"] if label[2] == "N included"
    ]
    if not total_n_labels:
        total_n_labels = [
            label for label in doc["labels"] if label[2] == "N participants"
        ]
    if len(total_n_labels) != 1:
        annotated_n[pmcid] = None
    elif len(total_n_labels[0]) == 4:
        annotated_n[pmcid] = int(total_n_labels[0][-1])
    else:
        start, stop, _ = total_n_labels[0]
        text = all_docs[pmcid]["text"][start:stop]
        annotated_n[pmcid] = int(text)

annotated_n = pd.Series(annotated_n).dropna()

if True:
    extracted_n = (
        participants_demographics.n_participants_from_labelbuddy_docs(
            [all_docs[pmcid] for pmcid in annotated_n.index]
        )
    )
    extracted_n = pd.Series(extracted_n, index=annotated_n.index)

else:
    extracted_n = scanning_horizon.n_participants_from_labelbuddy_docs(
        all_docs[pmcid] for pmcid in annotated_n.index
    )
    extracted_n = pd.Series(extracted_n, index=annotated_n.index)

kept = (annotated_n < annotated_n.quantile(0.9)) & (extracted_n.notnull())
# kept = extracted_n.notnull()
print(f"{kept.sum()} / {len(annotated_n)} found")
y_true, y_pred = annotated_n[kept].values, extracted_n[kept].values
# print(annotated_n[kept].sort_index())
for metric_name in (
    "r2_score",
    "mean_absolute_error",
    "median_absolute_error",
    "mean_absolute_percentage_error",
):
    print(metric_name, ":", getattr(metrics, metric_name)(y_true, y_pred))

plt.scatter(y_true, y_pred, alpha=0.3)
x_min, x_max = plt.gca().get_xlim()
y_min, y_max = plt.gca().get_ylim()
lims = min((x_min, y_min)), max((x_max, y_max))
plt.gca().set_xlim(lims)
plt.gca().set_ylim(lims)
plt.gca().set_aspect(1.0)
plt.gcf().savefig("/tmp/fig.png")
