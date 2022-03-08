import pprint
from participants import Reader, load_docs, _summarization

# doc = load_docs()[5]
# doc = load_docs()[1]
doc = load_docs()[21]
text = """

# Abstract

Twelve patients with total brachial plexus root avulsion underwent RS-fMRI after contralateral C7 nerve transfer. Seventeen healthy volunteers were also included in this fMRI study as controls. The hand motor seed regions were defined as region of interests in the bilateral hemispheres. The seed-based functional connectivity was calculated in all the subjects. Differences in functional connectivity of the motor cortical network between patients and healthy controls were compared.
"""
text = doc["text"]
extractor = Reader()
extracted = extractor.extract_from_text(text)
# list(map(print, map(str, extracted)))
# print(ie.ParticipantsGroup(*astuple(extracted[0])))
# pprint.pprint(extractor.extract_from_text(text))
# pprint.pprint(extractor._parser.parse(text))
res = _summarization.summarize(extracted)
print(repr(res))
print(res)
