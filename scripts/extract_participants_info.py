import pprint

from participants import Extractor, load_docs
from participants import _information_extraction as ie

doc = load_docs()[8]
extractor = Extractor()
pprint.pprint(extractor.extract_from_document(doc))
