from participants_demographics import extract_from_dataset


# input_f = "/home/data/no_backup/nqdc_data/query-30b352731ec276c226896665ca88ad5f/subset_articlesWithCoords_extractedData/text.csv"
# input_f = "/home/data/no_backup/nqdc_data/query-90f33493e7c1cb24fa7ad33c43bbe27f/subset_allArticles_extractedData/text.csv"
input_f = "/home/data/no_backup/nqdc_data/query-90f33493e7c1cb24fa7ad33c43bbe27f/subset_articlesWithCoords_extractedData/text.csv"
output_f = "/tmp/extracted_data.jsonl"


extract_from_dataset(input_f, output_f)
