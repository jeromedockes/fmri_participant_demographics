"""Evaluate sample size extraction."""
import pprint
import json

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn import neighbors

from matplotlib import pyplot as plt


import utils

EXCLUDED_IDX = np.arange(0, 20)


def get_y(samples, extractor_name, remove_outliers):
    result = {}
    extracted_n = samples.loc[:, extractor_name]
    annotated_n = samples.iloc[:, 0]
    if remove_outliers:
        detector = neighbors.LocalOutlierFactor(n_neighbors=20)
        kept_y_true = detector.fit_predict(annotated_n.values[:, None]) != -1
        true_median = np.percentile(annotated_n[kept_y_true].values, 50)
        kept = kept_y_true & extracted_n.notnull()
        result["n_annotations"] = int(kept_y_true.sum())
    else:
        kept = extracted_n.notnull()
        result["n_annotations"] = len(annotated_n)
        true_median = np.percentile(annotated_n.values, 50)
    result["n_detections"] = int(kept.sum())
    result["y_true"] = annotated_n[kept].values
    result["y_pred"] = extracted_n[kept].values
    result["true_median"] = true_median
    result["estimated_median"] = np.percentile(extracted_n[kept].values, 50)
    return result


def score_extraction(samples, extractor_name, remove_outliers):
    scores = {}
    y = get_y(samples, extractor_name, remove_outliers)
    scores["n_detections"] = y["n_detections"]
    scores["n_annotations"] = y["n_annotations"]
    scores["true_median"] = y["true_median"]
    scores["estimated_median"] = y["estimated_median"]
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


results_dir = utils.get_results_dir("n_participants")
samples = pd.read_csv(results_dir.joinpath("n_participants.csv"), index_col=0)
samples = samples.iloc[
    sorted(set(range(samples.shape[0])).difference(EXCLUDED_IDX))
]

all_scores = {}
for extractor_name in samples.columns[1:]:
    extractor_scores = {}
    for remove_outliers in (False, True):
        extractor_scores[
            f"remove_outliers_{remove_outliers}"
        ] = score_extraction(samples, extractor_name, remove_outliers)
    all_scores[extractor_name] = extractor_scores

results_dir.joinpath("scores.json").write_text(
    json.dumps(all_scores, indent=4), "utf-8"
)
pprint.pprint(all_scores)

for remove_outliers in (False, True):
    fig, axes = plt.subplots(1, 2, sharex=True, sharey=True)
    xy_min, xy_max = 0, 0
    for ax, extractor_name in zip(axes, all_scores.keys()):
        y = get_y(samples, extractor_name, remove_outliers)
        ax.set_title(
            f"{extractor_name}\n"
            f"{y['n_detections']} / {y['n_annotations']} detections"
        )
        ax.scatter(y["y_true"], y["y_pred"], alpha=0.3)
        xy_min = min((xy_min, ax.get_xlim()[0], ax.get_ylim()[0]))
        xy_max = max((xy_max, ax.get_xlim()[1], ax.get_ylim()[1]))
        ax.set_aspect(1.0)
    axes[0].set_xlim((xy_min, xy_max))
    for ax in axes:
        ax.plot([xy_min, xy_max], [xy_min, xy_max])
    fig.savefig(
        results_dir.joinpath(f"remove_outliers_{remove_outliers}.png"),
        bbox_inches="tight",
    )
