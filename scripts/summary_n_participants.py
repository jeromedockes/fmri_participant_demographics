import utils

demographics_data = utils.load_n_participants(0)
demographics_data["publication_year"] = demographics_data[
    "publication_year"
].dt.year
demographics_data.to_csv(
    utils.get_outputs_dir() / "n_participants_full_dataset.csv"
)
