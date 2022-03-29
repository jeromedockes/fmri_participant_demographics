import argparse

from participants_demographics import extract_from_dataset

import utils

parser = argparse.ArgumentParser()
parser.add_argument("articles_csv")
args = parser.parse_args()


extract_from_dataset(args.articles_csv, utils.get_demographics_file())
