from pubextract import participants

import utils


participants.extract_from_dataset(
    utils.get_pubget_data_dir() / "text.csv", utils.get_demographics_file()
)
