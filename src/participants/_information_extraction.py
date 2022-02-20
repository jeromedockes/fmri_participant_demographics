from pathlib import Path
import re
from typing import List, Tuple

from lark import Lark, Transformer


def _get_parser(start="participants", ambiguity="explicit") -> Lark:
    grammar = (
        Path(__file__)
        .parent.joinpath("_data", "n_participants_grammar.lark")
        .read_text("utf-8")
    )
    parser = Lark(grammar, start=start, ambiguity=ambiguity)
    return parser


class ParticipantsTransformer(Transformer):
    def INT(self, n):
        return int(n.value), n.start_pos, n.end_pos

    def digit_number(self, n):
        return dict(zip(("value", "start_pos", "end_pos"), n[0]))

    def UNIT_NAME(self, n):
        value = (
            "zero one two three four five six seven eight nine".split().index(
                str(n)
            )
        )
        return value, n.start_pos, n.end_pos

    def unit_text_number(self, n):
        return n[0]

    def unit_part(self, n):
        return n[0]

    def DOZEN_NAME(self, n):
        value = (
            "zero ten twenty thirty fourty fifty sixty "
            "seventy eighty ninety".split().index(str(n))
        ) * 10
        return value, n.start_pos, n.end_pos

    def TEEN_NAME(self, n):
        value = (
            "ten eleven twelve thirteen fourteen fifteen sixteen "
            "seventeen eighteen nineteen".split().index(str(n)) + 10
        )
        return value, n.start_pos, n.end_pos

    def dozen_text_number(self, n):
        value = sum(p[0] for p in n if p is not None)
        start = min(p[1] for p in n if p is not None)
        end = max(p[2] for p in n if p is not None)
        return value, start, end

    def dozen_part(self, n):
        return n[0]

    def hundred_part(self, n):
        value = 100 * n[0][0]
        return value, n[0][1], n[0][2]

    def hundred_text_number(self, n):
        value = sum(p[0] for p in n if p is not None)
        start = min(p[1] for p in n if p is not None)
        end = max(p[2] for p in n if p is not None)
        return value, start, end

    def text_number(self, n):
        return dict(zip(("value", "start_pos", "end_pos"), n[0]))

    def participants_desc(self, desc):
        return dict(zip(("value", "start_pos", "end_pos"), desc[-1]))

    def PARTICIPANTS_NAME(self, name):
        return name.value, name.start_pos, name.end_pos

    def participants_inline(self, part):
        return {"n_participants": part[1], "participants_name": part[2]}

    def participants_n(self, part):
        return {"n_participants": part[1], "participants_name": part[0]}

    def participants(self, part):
        return part[0]

    def extra_text(self, extra):
        return " ".join(extra)

    def age_info(self, info):
        return info[0]

    def age_mean_std(self, info):
        return {
            "age_mean": float(info[0].value),
            "start_pos": info[0].start_pos,
            "end_pos": info[0].end_pos,
        }

    def age_mean(self, info):
        return {
            "age_mean": float(info[0].value),
            "start_pos": info[0].start_pos,
            "end_pos": info[0].end_pos,
        }

    def participants_subgroup_n(self, info):
        return {
            "n_subgroup": info[0]["value"],
            "subgroup_name": info[1].value,
            "start_pos": info[0]["start_pos"],
            "end_pos": info[1].end_pos,
        }

    def participants_details(self, details):
        return [d for d in details if d is not None]

    def age_range(self, info):
        return {
            "age_range": (info[0][0], info[2][0]),
            "start_pos": info[0][1],
            "end_pos": info[2][2],
        }

    def extra_detail(self, extra):
        return None


class Extractor:
    def __init__(self):
        self._parser = _get_parser()
        self._details_parser = _get_parser(
            start="participants_details", ambiguity="resolve"
        )
        self._transformer = ParticipantsTransformer()

    def extract_from_snippet(self, text):
        tree = self._parser.parse(text.lower())
        transformed = self._transformer.transform(tree)
        if hasattr(transformed, "children"):
            children = sorted(
                transformed.children,
                key=lambda c: (
                    -c["n_participants"]["end_pos"],
                    c["n_participants"]["start_pos"],
                ),
            )
            result = children[0]
        else:
            result = transformed
        start_pos = min([c["start_pos"] for c in result.values()])
        end_pos = max([c["end_pos"] for c in result.values()])
        result.update({"start_pos": start_pos, "end_pos": end_pos})
        return result

    def extract_details(self, snippet):
        all_extracted = []
        for match in re.finditer(r"(\([^)]+\))", snippet):
            extracted = self._transformer.transform(
                self._details_parser.parse(match.group(1))
            )
            if extracted:
                all_extracted.append(extracted)
        return all_extracted

    def extract_from_document(self, document):
        all_sections = _get_participants_sections(document["text"])
        result = []
        for section in all_sections:
            extracted_from_section = []
            all_parts = _split_participants_section(*section)
            for part, part_start, part_end in all_parts:
                try:
                    extracted = self.extract_from_snippet(part)
                except Exception:
                    pass
                else:
                    extracted["start_pos"] += part_start
                    extracted["end_pos"] += part_start
                    extracted["text"] = document["text"][
                        extracted["start_pos"] : extracted["end_pos"]
                    ]
                    extracted["section"] = section[0].strip()
                    for child in extracted.values():
                        try:
                            child["start_pos"] += part_start
                            child["end_pos"] += part_start
                        except (TypeError, KeyError):
                            pass
                    extracted_from_section.append(extracted)
            for i in range(len(extracted_from_section) - 1):
                extracted_from_section[i]["details"] = self.extract_details(
                    document["text"][
                        extracted_from_section[i][
                            "start_pos"
                        ] : extracted_from_section[i + 1]["end_pos"]
                    ]
                )
            if extracted_from_section:
                extracted_from_section[-1]["details"] = self.extract_details(
                    document["text"][
                        extracted_from_section[-1]["start_pos"] : section[-1]
                    ]
                )

            result.extend(extracted_from_section)
        return result


def _get_participants_sections(
    article_text: str,
) -> List[Tuple[str, str, int, int]]:
    sections = []
    for sec in re.finditer(
        r"^#+ ([^\n]*(?:participants?|subjects?|abstract)[^\n]*)"
        r"(.*?)(?:\n\n\n|^#)",
        article_text,
        flags=re.I | re.MULTILINE | re.DOTALL,
    ):
        sections.append((sec.group(1), sec.group(2), sec.start(2), sec.end(2)))
    return sections


_PARTICIPANTS_NAME = (
    r"(participants|subjects|controls|patients|volunteers|individuals"
    "|adults|children|adolescents|men|women|males|male|females|female)"
)


def _split(section, flags):
    parts = []
    start = 0
    match = None
    for match in re.finditer(
        rf"(?:[^()]|\([^)]+\))*?{_PARTICIPANTS_NAME}", section, flags=flags
    ):
        parts.append(section[start : match.start(1)])
        parts.append(section[match.start(1) : match.end(1)])
        start = match.end(1)
    if match is not None:
        parts.append(section[match.end(1) :])
    return parts


def _split_participants_section(
    section_name: str, section: str, section_start: str, section_end: str
) -> List[Tuple[str, int, int]]:
    all_parts = _split(section, re.I)
    concatenated_parts = []
    start, end = section_start, section_end
    for idx in range(1, len(all_parts) - 1, 2):
        end += len(all_parts[idx - 1]) + len(all_parts[idx])
        concatenated_parts.append(
            (all_parts[idx - 1] + all_parts[idx], start, end)
        )
        start += len(all_parts[idx - 1])
        end += len(all_parts[idx + 1])
        concatenated_parts.append(
            (all_parts[idx] + all_parts[idx + 1], start, end)
        )
        start += len(all_parts[idx])
    return concatenated_parts
