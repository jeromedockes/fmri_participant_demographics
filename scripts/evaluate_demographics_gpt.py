import pprint
import pandas as pd
from publang.evaluate import score_columns, hungarian_match_compare 
import utils

# Load evaluation annotations
annotations = pd.read_csv(utils.get_outputs_dir() / 'evaluation_labels.csv')
predictions_gpt = pd.read_csv(utils.get_outputs_dir() / 'participant_demographics_gpt_tokens-2000.csv')
# predictions_gpt_4000 = pd.read_csv(utils.get_outputs_dir() / 'participant_demographics_gpt_tokens-4000.csv')


def _evaluate(annotations, predictions):

    # Match compare
    match_compare = hungarian_match_compare(annotations, predictions)

    # Compare by columns (matched accuracy)
    res_mean, res_sums, counts = score_columns(annotations, predictions)

    # Subset to only pmcids in predictions
    diff = set(set(annotations.pmcid.unique()) - set(predictions.pmcid.unique()))
    annotations = annotations[annotations.pmcid.isin(predictions.pmcid.unique())]

    # Compute overlap of pmcids
    pred_n_groups = predictions.groupby('pmcid').size()
    n_groups = annotations.groupby('pmcid').size()
    correct_n_groups = (n_groups == pred_n_groups)
    more_groups_pred = (n_groups < pred_n_groups)
    less_groups_pred = (n_groups > pred_n_groups)

    print(f"Exact match # of groups: {correct_n_groups.mean():.2f}\n",
    f"More groups predicted: {more_groups_pred.mean():.2f}\n",
    f"Less groups predicted: {less_groups_pred.mean():.2f}\n",
    f"Missing pmcids: {diff}\n"
    )

    # Compare by columns (matched accuracy)
    print("Column wise comparison of predictions and annotations (error):\n")
    pprint.pprint(match_compare)

    # Compare by columns (count of pmcids with overlap)
    print("\nPercentage response given by pmcid:\n")
    pprint.pprint(counts)


    # Compare by columns (summed mean percentage error on sum by pmcid)
    print("\nSummed Mean percentage error:\n")
    pprint.pprint(res_mean)

    # Compare by columns (summed mean percentage error on mean by pmcid)
    print("\nAveraged Mean percentage error:\n")
    pprint.pprint(res_sums)

    return match_compare, res_mean, res_sums, counts


print("Evaluate GPT with smaller chunk size (2000)")
match_compare, res_mean, res_sums, counts = _evaluate(annotations, predictions_gpt)

# print("Evaluate GPT with smaller chunk size (4000)")
# match_compare, res_mean, res_sums, counts = _evaluate(annotations, predictions_gpt_4000)