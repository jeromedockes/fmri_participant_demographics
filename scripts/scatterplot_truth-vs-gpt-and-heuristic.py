import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd

import utils


np.random.seed(0)

demographics_file = utils.get_outputs_dir() / "n_participants_full_dataset.csv"
heuristic_data = pd.read_csv(demographics_file).set_index("pmcid")
heuristic_data["heuristic"] = heuristic_data["count"]

#  gpt data
gpt_file = (
    utils.get_outputs_dir()
    # / "all_documents_participant_demographics_gpt_tokens-4000_clean.csv"
    / "eval_participant_demographics_gpt_tokens-2000_clean.csv"
)
gpt_data_original = pd.read_csv(gpt_file)
gpt_data = pd.DataFrame(index=gpt_data_original["pmcid"].unique())
# calculate total count for multi-group studies
# (there is one row per group in the original data)
for pmcid, group in gpt_data_original.groupby("pmcid"):
    gpt_data.loc[pmcid, "gpt"] = group["count"].sum()
    gpt_data.loc[pmcid, "n_groups"] = len(group)


# ground truth
truth_file = utils.get_outputs_dir() / "evaluation_labels.csv"
truth_data_original = pd.read_csv(truth_file)
truth_data = pd.DataFrame(index=truth_data_original["pmcid"].unique())
for pmcid, group in truth_data_original.groupby("pmcid"):
    truth_data.loc[pmcid, "truth"] = group["count"].sum()
    truth_data.loc[pmcid, "n_groups"] = len(group)

# concatenate data to compare results
data_full = pd.concat(
    [
        heuristic_data,
        gpt_data,
        truth_data,
    ],
    axis=1,
    join="outer",
)
# data_full.to_csv('TEMP.csv')

data = data_full.loc[:, ["heuristic", "gpt", "truth"]]
data = data[data.index.isin(truth_data.index)]

# evaluate results
pe_guessed = len(data[data["heuristic"] > -1])/len(data) * 100
gpt_guessed = len(data[data["gpt"] > -1])/len(data) * 100
print(f'\nheuristic made a guess in {pe_guessed} % of evaluation papers')
print(f'GPT made a guess in {gpt_guessed} % of evaluation papers\n')

pe_mape = np.nanmedian(np.abs(data.heuristic - data.truth) / data.truth) * 100
gpt_mape = np.nanmedian(np.abs(data.gpt - data.truth) / data.truth) * 100
print(f'heuristic MAPE: {pe_mape}')
print(f'GPT MAPE: {gpt_mape}\n')

pe_mae = np.nanmedian(np.abs(data.heuristic - data.truth))
gpt_mae = np.nanmedian(np.abs(data.gpt - data.truth))
print(f'heuristic MAE: {pe_mae}')
print(f'GPT MAE: {gpt_mae}\n')

pe_correct = len(data[data.heuristic == data.truth]) / len(data) * 100
gpt_correct = len(data[data.gpt == data.truth]) / len(data) * 100
print(f'heuristic was correct in {pe_correct} % of all papers')
print(f'GPT was correct in {gpt_correct} % of all papers\n')

median_heuristic = data["heuristic"].median()
median_gpt = data["gpt"].median()
median_truth = data["truth"].median()
print(f"Median of heuristic counts: {median_heuristic}")
print(f"Median of GPT-3 counts: {median_gpt}")
print(f"Median of ground truth counts: {median_truth}")

# create figure
fig, ax = plt.subplots(figsize=(5, 5))
sns.scatterplot(
    data=data,
    x="heuristic",
    y="truth",
    ax=ax,
    label="heuristic",
    alpha=.7,
)


sns.scatterplot(
    data=data,
    x="gpt",
    y="truth",
    ax=ax,
    label="GPT-3",
    alpha=.7,
)
ax.scatter(
    median_heuristic,
    median_truth,
    color='tab:blue',
    marker='*',
    s=200,
    label="Median of heuristic counts",
    alpha=.7,
    edgecolors='k'
)
ax.scatter(
    median_gpt,
    median_truth,
    color='tab:orange',
    marker='*',
    s=200,
    label="Median of GPT-3 counts",
    alpha=.7,
    edgecolors='k'
)

ax.set_xlabel(
    "Participant count\n(automatically extracted by heuristic or GPT-3)"
)
ax.set_ylabel("Participant count\n(manually-labelled ground truth)")
ax.set_yscale('log')
ax.set_xscale('log')
ax.set_aspect('equal')
ax.plot([0.9, 1000], [0.9, 1000], color='k', alpha=.2, linestyle='--')
ax.set_ylim([0.9, 1000])
ax.set_xlim([0.9, 1000])
ax.set_title("All studies")
sns.despine()
plt.legend(loc="lower right")

fig.tight_layout()
fig.savefig(
    utils.get_figures_dir()
    / "scatterplot_labels_vs_gpt_and_heuristic_multi_and_single_groups.pdf"
)
