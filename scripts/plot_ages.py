"""Plot age distribution of all participants and by category (patients/controls)."""
import json

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns

import utils


age_means = []
detailed_age_means = []
with open(utils.get_demographics_file(), encoding="utf-8") as demo_f:
    for article_json in demo_f:
        article_info = json.loads(article_json)
        age_means.append(article_info["demographics"]["age_mean"])
        for group in article_info["demographics"]["groups"]:
            detailed_age_means.append(
                {
                    "Participant type": group["participant_type"].capitalize(),
                    "age_mean": group["age_mean"],
                }
            )
detailed_age_means = pd.DataFrame(detailed_age_means).dropna()


fig, ax = plt.subplots(figsize=(4,3))
sns.kdeplot(
    data=detailed_age_means,
    x="age_mean",
    ax=ax,
    hue="Participant type",
    common_norm=False,
)

ax.set_xlabel("Mean age in group of participants")
ax.set_yticks([])
xmin, xmax = ax.get_xlim()
ax.set_xlim(0, xmax)
sns.despine()
sns.move_legend(ax, "upper right", frameon=False)
# ax.legend(loc="upper right", frameon=False)

out_dir = utils.get_figures_dir()
fig.savefig(out_dir / f"ages_distrib_detailed.pdf", bbox_inches="tight")
plt.close("all")


fig, ax = plt.subplots()
sns.histplot(x=age_means, ax=ax, kde=True, stat="probability")
ax.set_xlabel("Mean age of study participants")
fig.savefig(out_dir / f"ages_distrib.pdf", bbox_inches="tight")
