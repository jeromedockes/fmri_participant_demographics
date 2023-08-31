"""Evaluate sample size extraction."""
import pprint
import json

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn import neighbors

from matplotlib import pyplot as plt


import utils

EXCLUDED_IDX = json.loads(
    (utils.get_repo_data_dir() / "training_pmcids.json").read_text("UTF-8")
)["annotated_pmcids"]

def get_y(samples, extractor_name):
    result = {}
    extracted_n = samples.loc[:, extractor_name]
    annotated_n = samples.iloc[:, 0]
    kept = extracted_n.notnull()
    result["n_annotations"] = len(annotated_n)
    true_median = np.percentile(annotated_n.values, 50)
    result["n_detections"] = int(kept.sum())
    result["y_true"] = annotated_n[kept].values
    result["y_pred"] = extracted_n[kept].values
    result["true_median"] = true_median
    result["estimated_median"] = np.percentile(extracted_n[kept].values, 50)
    return result


def score_extraction(samples, extractor_name):
    scores = {}
    y = get_y(samples, extractor_name)
    scores["n_detections"] = y["n_detections"]
    scores["n_annotations"] = y["n_annotations"]
    scores["true_median"] = y["true_median"]
    scores["estimated_median"] = y["estimated_median"]
    scores["n_errors"] = int((y["y_true"] != y["y_pred"]).sum())
    abs_errors = np.abs(y["y_true"] - y["y_pred"]) / y["y_true"]
    percentile_90_abs_error = np.percentile(abs_errors, 90)
    scores["percentile_90_abs_error"] = percentile_90_abs_error
    percentile_80_abs_error = np.percentile(abs_errors, 80)
    scores["percentile_80_abs_error"] = percentile_80_abs_error
    for metric_name in (
        "r2_score",
        "mean_absolute_error",
        "median_absolute_error",
        "mean_absolute_percentage_error",
    ):
        scores[metric_name] = getattr(metrics, metric_name)(
            y["y_true"], y["y_pred"]
        )
    return scores


samples = pd.read_csv(
    utils.get_outputs_dir() / "n_participants.csv", index_col=0
)
print(samples[samples["annotations"] >= 1000])
samples = samples.loc[list(set(samples.index) - set(EXCLUDED_IDX))].dropna(
    subset="annotations")

all_scores = {}
for extractor_name in samples.columns[1:]:
    all_scores[extractor_name] = score_extraction(samples, extractor_name)

(utils.get_outputs_dir() / "extraction_scores.json").write_text(
    json.dumps(all_scores, indent=4), "utf-8"
)
pprint.pprint(all_scores)

fig, axes = plt.subplots(1, 3, sharex=True, sharey=True)
xy_min, xy_max = 0, 0
for ax, extractor_name in zip(axes, all_scores.keys()):
    y = get_y(samples, extractor_name)
    ax.set_title(
        f"{extractor_name}\n"
        f"{y['n_detections']} / {y['n_annotations']} detections\n"
        f"Median Absolute Error: {all_scores[extractor_name]['median_absolute_error']:.1f}"
    )
    ax.scatter(y["y_true"], y["y_pred"], alpha=0.3)
    xy_min = min((xy_min, ax.get_xlim()[0], ax.get_ylim()[0]))
    xy_max = max((xy_max, ax.get_xlim()[1], ax.get_ylim()[1]))
    ax.set_aspect(1.0)
    ax.set_xlabel("True participant count")
axes[0].set_xlim((xy_min, xy_max))
axes[0].set_ylabel("Extracted participant count")
for ax in axes:
    ax.plot([xy_min, xy_max], [xy_min, xy_max])
fig.savefig(
    utils.get_figures_dir() / ("extraction_scatterplot.pdf"),
    bbox_inches="tight",
)

# Calculate scores on interseciton between the 3 approaches
samples_nona = samples.dropna()

all_score_nona = {}
for extractor_name in samples.columns[1:]:
    all_score_nona[extractor_name] = score_extraction(samples_nona, extractor_name)

(utils.get_outputs_dir() / "extraction_scores_nona.json").write_text(
    json.dumps(all_score_nona, indent=4), "utf-8"
)
print("Scores on intersection of all 3 approaches:")
pprint.pprint(all_score_nona)

fig, axes = plt.subplots(1, 3, sharex=True, sharey=True)
xy_min, xy_max = 0, 0
for ax, extractor_name in zip(axes, all_score_nona.keys()):
    y = get_y(samples, extractor_name)
    ax.set_title(
        f"{extractor_name}\n"
        f"{y['n_detections']} / {y['n_annotations']} detections\n"
        f"Median Absolute Error: {all_score_nona[extractor_name]['median_absolute_error']:.1f}"
    )
    ax.scatter(y["y_true"], y["y_pred"], alpha=0.3)
    xy_min = min((xy_min, ax.get_xlim()[0], ax.get_ylim()[0]))
    xy_max = max((xy_max, ax.get_xlim()[1], ax.get_ylim()[1]))
    ax.set_aspect(1.0)
    ax.set_xlabel("True participant count")
axes[0].set_xlim((xy_min, xy_max))
axes[0].set_ylabel("Extracted participant count")
for ax in axes:
    ax.plot([xy_min, xy_max], [xy_min, xy_max])
fig.savefig(
    utils.get_figures_dir() / ("extraction_scatterplot_nona.pdf"),
    bbox_inches="tight",
)
