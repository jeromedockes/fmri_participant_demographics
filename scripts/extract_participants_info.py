import pprint
from dataclasses import astuple

from participants import Extractor, load_docs
from participants import _information_extraction as ie

doc = load_docs()[0]
text = """

# Abstract

there were 21 participants (something, age 12 - 89 years, 8 males) and some  healthy new young patients (n=34) and one hundred and twenty-six healthy volunteers (80 females, 90 males, age: 54 ± 3.4 years)
"""
text = doc["text"]
extractor = Extractor()
extracted = extractor.extract_from_text(text)
list(map(print, map(str, extracted)))
# print(ie.ParticipantsGroup(*astuple(extracted[0])))
# pprint.pprint(extractor.extract_from_text(text))
# pprint.pprint(extractor._parser.parse(text))
