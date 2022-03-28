import json

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns

demographics_file = "/tmp/extracted_data.jsonl"

age_means = []
detailed_age_means = []
with open(demographics_file, encoding="utf-8") as demo_f:
    for article_json in demo_f:
        article_info = json.loads(article_json)
        age_means.append(article_info["demographics"]["age_mean"])
        for group in article_info["demographics"]["groups"]:
            detailed_age_means.append(
                {
                    "participant_type": group["participant_type"],
                    "age_mean": group["age_mean"],
                }
            )
detailed_age_means = pd.DataFrame(detailed_age_means).dropna()

fig, ax = plt.subplots()
sns.kdeplot(
    data=detailed_age_means,
    x="age_mean",
    ax=ax,
    hue="participant_type",
    common_norm=False,
)
ax.set_xlabel("Mean age in group of participants")
fig.savefig("/tmp/ages_distrib_detailed.png", bbox_inches="tight")


fig, ax = plt.subplots()
sns.histplot(x=age_means, ax=ax, kde=True, stat="probability")
ax.set_xlabel("Mean age of study participants")
fig.savefig("/tmp/ages_distrib.png", bbox_inches="tight")
