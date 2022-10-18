from pathlib import Path

import pandas as pd

from nimf.data import constants
from nimf import datasets

from participants_demographics import _reading
import participants_demographics


class TextToNumber:
    def __init__(self):
        self.parser = _reading._get_parser(
            start="number", ambiguity="resolve", grammar="numbers_grammar"
        )
        self.transformer = _reading.ParticipantsTransformer(0)

    def __call__(self, text):
        try:
            parse_tree = self.parser.parse(text)
            return self.transformer.transform(parse_tree).value
        except Exception:
            return None


# load the annotations
anns = datasets.read_annotations(
    annotations_path=constants.PATH_TO_FOLDER_WITH_ANNOTATIONS
    / "labelled_texts_kendra.jsonl",
    add_text=True,
    docs_path=constants.PATH_TO_ALL_DOCS,
)

pmids_and_pmcids = pd.read_csv(constants.PATH_TO_OPEN_FMRI_PMIDS_AND_PMCIDS)

df = pd.DataFrame(
    index=range(len(anns)),
    columns=[
        "pmcid",
        "annotated_n",
        "annotated_sentence",
        "i_start_n_in_A_sentence",
        "i_end_n_in_A_sentence",
        "extracted_n_text",
        "extracted_n",
        "extracted_sentence",
        "i_start_n_in_E_sentence",
        "i_end_n_in_E_sentence",
    ],
)

text_to_number = TextToNumber()

# get Ns and sentences from annotations
for i_doc, doc in enumerate(anns):
    pmid = doc["metadata"]["pmid"]
    pmcid = int(pmids_and_pmcids[pmids_and_pmcids["pmid"] == pmid]["pmcid"])
    df.at[i_doc, "pmcid"] = pmcid

    text = doc["text"]
    anns = doc["annotations"]
    for ann in anns:
        if ann["label_name"] == "n_participants_total":
            # save the annotated number of participants
            i_start_n, i_end_n = ann["start_char"], ann["end_char"]
            n_str = text[i_start_n:i_end_n]
            n_int = text_to_number(n_str)
            df.at[i_doc, "annotated_n"] = n_int

            # save the sentence where we annotated the number of participants
            i_start_sentence = text[:i_start_n].rfind(". ") + 1
            i_end_sentence = text[i_end_n:].find(". ") + i_end_n + 1
            df.at[i_doc, "annotated_sentence"] = text[i_start_sentence:i_end_sentence]

            # save the start and end indices of N within the sentence
            df.at[i_doc, "i_start_n_in_A_sentence"] = i_start_n - i_start_sentence
            df.at[i_doc, "i_end_n_in_A_sentence"] = (i_start_n - i_start_sentence) + (
                i_end_n - i_start_n
            )

df = df[df["annotated_n"].notna()]
df = df.set_index("pmcid")

# get extracted Ns and the sentences they come from

# load the extracted data
docs = list(datasets.load_docs_in_nqdc_format(pmcids=list(df.index)))
extractions = participants_demographics.annotate_labelbuddy_docs(docs)
extracted_n = participants_demographics.n_participants_from_labelbuddy_docs(docs)

pmcids = []
[pmcids.append(doc["metadata"]["pmcid"]) for doc in docs]
docs_df_full = pd.DataFrame(docs)
docs_df = pd.DataFrame(data=list(docs_df_full["text"]), columns=["text"], index=pmcids)

for i_ext, ext in enumerate(extractions):
    pmcid = int(ext["metadata"]["pmcid"])
    text = docs_df.at[pmcid, "text"]
    for ann in ext["annotations"]:
        if ann["end_char"] != 0:
            if ann["label_name"] == "ParticipantsGroupInfo":
                i_start_n = ann["start_char"]
                i_end_n = ann["end_char"]
                n_str = text[i_start_n:i_end_n]
                df.at[pmcid, "extracted_n_text"] = n_str
                df.at[pmcid, "extracted_n"] = extracted_n[i_ext]

                # save the sentence where we annotated the number of participants
                i_start_sentence = text[:i_start_n].rfind(". ") + 1
                i_end_sentence = text[i_end_n:].find(". ") + i_end_n + 1
                df.at[pmcid, "extracted_sentence"] = text[
                    i_start_sentence:i_end_sentence
                ]

                # save the start and end indices of N within the sentence
                df.at[pmcid, "i_start_n_in_E_sentence"] = i_start_n - i_start_sentence
                df.at[pmcid, "i_end_n_in_E_sentence"] = (
                    i_start_n - i_start_sentence
                ) + (i_end_n - i_start_n)

df.to_csv(Path(__file__).resolve().parent / "compare_n_participants_KENDRA_data.csv")
