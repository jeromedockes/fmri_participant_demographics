from participants import Extractor, load_docs
from participants import _information_extraction as ie

print([d["meta"]["pmcid"] for d in load_docs()[:3]])

doc = load_docs()[18]
extractor = Extractor()

all_sections = ie._get_participants_sections(doc["text"])
for section_name, section in all_sections:
    print(f"\n{section_name}\n=================")
    all_parts = ie._split_participants_section(section)
    for part in all_parts:
        # print('---')
        try:
            # print(part)
            extracted = extractor.extract(part)
            print()
            print(extracted)
        except Exception:
            # print(f"{part} did not match")
            print(".", end="")
    print()
