import json

from pubextract.participants import annotate_labelbuddy_docs
import utils

output_file = utils.get_outputs_dir() / "automatically_annotated_docs.json"
docs = utils.load_labelbuddy_docs()
annotated_docs = [doc for doc, _ in annotate_labelbuddy_docs(docs)]

output_file.write_text(json.dumps(annotated_docs), "utf-8")

print(output_file)
