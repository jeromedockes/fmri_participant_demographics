import pandas as pd

import participants_demographics
import scanning_horizon
import utils


annotations = utils.load_annotations("annotations_jerome.jsonl")
all_docs = utils.load_docs()
annotated_n = pd.Series(
    utils.n_participants_from_annotations(annotations, all_docs)
).dropna()

samples = pd.DataFrame({"annotations": annotated_n})
samples.index.name = "pmcid"

for extractor in (participants_demographics, scanning_horizon):
    print(extractor.__name__)
    extracted_n = pd.Series(
        extractor.n_participants_from_labelbuddy_docs(
            [all_docs[pmcid] for pmcid in annotated_n.index]
        ),
        index=annotated_n.index,
    )
    samples[extractor.__name__] = extracted_n

results_dir = utils.get_results_dir("n_participants")
samples.to_csv(results_dir.joinpath("n_participants.csv"))
#     extractor_results["extracted_n"] = extracted_n
#     extractor_results["annotated_n"] = annotated_n
#     kept = (annotated_n < annotated_n.quantile(0.9)) & (extracted_n.notnull())
#     # kept = extracted_n.notnull()
#     print(f"{kept.sum()} / {len(annotated_n)} found")
#     y_true, y_pred = annotated_n[kept].values, extracted_n[kept].values
#     scores = {}
#     for metric_name in (
#         "r2_score",
#         "mean_absolute_error",
#         "median_absolute_error",
#         "mean_absolute_percentage_error",
#     ):
#         scores[metric_name] = getattr(metrics, metric_name)(y_true, y_pred)
#     extractor_results["scores"] = scores
#     results[extractor.__name__] = extractor_results

# print({k: v["scores"] for (k, v) in results.items()})
# plt.scatter(y_true, y_pred, alpha=0.3)
# x_min, x_max = plt.gca().get_xlim()
# y_min, y_max = plt.gca().get_ylim()
# lims = min((x_min, y_min)), max((x_max, y_max))
# plt.gca().set_xlim(lims)
# plt.gca().set_ylim(lims)
# plt.gca().set_aspect(1.0)
# plt.gcf().savefig("/tmp/fig.png")
