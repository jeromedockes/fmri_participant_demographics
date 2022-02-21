import pprint

from participants import Extractor, load_docs
from participants import _information_extraction as ie

doc = load_docs()[3]
text = """

# Abstract

there were 21 participants (something) and some  healthy new young patients (n = 34)
"""
text = doc["text"]
extractor = Extractor()
pprint.pprint(extractor.extract_from_text(text))
# pprint.pprint(extractor._parser.parse(text))
