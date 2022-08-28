"""Extract demographic information and store in JSON format."""
from participants_demographics import extract_from_dataset

import utils


extract_from_dataset(
    utils.get_nqdc_data_dir().joinpath("text.csv"),
    utils.get_demographics_file(),
)
