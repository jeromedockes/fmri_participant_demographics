"""Report the values corresponding to those provided in the Poldrack & al text.

Original values:
- median N:
  - 28.5 for single-group in 2015
  - 19 subjects / group in multiple studies in 2015
- n studies with N > 100: 8 in 2012, 17 in 2015
"""
import pandas as pd

import utils

data = utils.load_n_participants(0)
print(f"n papers: {data.shape[0]}")
n_papers_large_sample = (
    data[data["count"] > 100].groupby("publication_year")["count"].count()
)
n_papers = data.groupby("publication_year")["count"].count()
n_papers_df = pd.DataFrame(
    {"N > 100": n_papers_large_sample, "All": n_papers}
).fillna(0)
n_papers_df["proportion"] = n_papers_df["N > 100"] / n_papers_df["All"]
print(n_papers_df)
group_counts = data.groupby("publication_year")[
    "count", "patient_count", "healthy_count"
].median()
single_group_count = (
    data[data["n_groups"] == 1].groupby("publication_year")["count"].median()
)
group_counts["single_group_count"] = single_group_count
print(group_counts)
# print(data.groupby("publication_year")["count"].count())
