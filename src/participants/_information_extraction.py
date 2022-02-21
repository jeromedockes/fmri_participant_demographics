from pathlib import Path
import re
from typing import List, Tuple

from lark import Lark, Transformer, Discard


def _get_parser(start="participants", ambiguity="explicit") -> Lark:
    grammar = (
        Path(__file__)
        .parent.joinpath("_data", "n_participants_grammar.lark")
        .read_text("utf-8")
    )
    parser = Lark(grammar, start=start, ambiguity=ambiguity)
    return parser


def _triplet_to_dict(triplet):
    return dict(zip(("value", "start_pos", "end_pos"), triplet))


class ParticipantsTransformer(Transformer):
    def INT(self, n):
        return int(n.value), n.start_pos, n.end_pos

    def digit_number(self, n):
        return _triplet_to_dict(n[0])

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
        return _triplet_to_dict(n[0])

    def participants_desc(self, desc):
        return _triplet_to_dict(desc[-1])

    def PARTICIPANTS_NAME(self, name):
        return name.value, name.start_pos, name.end_pos

    def participants_inline(self, part):
        return {"n_participants": part[1], "participants_name": part[2]}

    def PARTICIPANTS_ADJ(self, adj):
        return adj.value, adj.start_pos, adj.end_pos

    def participants_n(self, part):
        res = {
            "n_participants": _triplet_to_dict(part[4]),
            "participants_name": _triplet_to_dict(part[3]),
        }
        if part[1] is not None:
            res["participants_adj"] = _triplet_to_dict(part[1])
        return res

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
        return details

    def age_range(self, info):
        return {
            "age_range": (info[0][0], info[2][0]),
            "start_pos": info[0][1],
            "end_pos": info[2][2],
        }

    def extra_detail(self, extra):
        return Discard

    def DETAIL_SEP(self, sep):
        return Discard


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
                all_extracted.extend(extracted)
        return all_extracted

    def extract_from_text(self, text):
        all_sections = _get_participants_sections(text)
        result = []
        for (
            section_name,
            section_text,
            section_start,
            section_end,
        ) in all_sections:
            extracted_from_section = []
            all_parts = _split_participants_section(
                section_text, section_start
            )
            for part, part_start, part_end in all_parts:
                try:
                    extracted = self.extract_from_snippet(part)
                except Exception:
                    pass
                else:
                    extracted["start_pos"] += part_start
                    extracted["end_pos"] += part_start
                    extracted["text"] = text[
                        extracted["start_pos"] : extracted["end_pos"]
                    ]
                    extracted["section"] = section_name.strip()
                    for child in extracted.values():
                        try:
                            child["start_pos"] += part_start
                            child["end_pos"] += part_start
                        except (TypeError, KeyError):
                            pass
                    extracted_from_section.append(extracted)
            for i in range(len(extracted_from_section) - 1):
                extracted_from_section[i]["details"] = self.extract_details(
                    text[
                        extracted_from_section[i][
                            "start_pos"
                        ] : extracted_from_section[i + 1]["end_pos"]
                    ]
                )
            if extracted_from_section:
                extracted_from_section[-1]["details"] = self.extract_details(
                    text[extracted_from_section[-1]["start_pos"] : section_end]
                )

            result.extend(extracted_from_section)
        return result


def _get_participants_sections(
    article_text: str,
) -> List[Tuple[str, str, int, int]]:
    sections = []
    for sec in re.finditer(
        r"^#+ ([^\n]*(?:participants?|subjects?|abstract)[^\n]*)"
        r"(.*?)(?:\n\n\n|^#|\Z)",
        article_text,
        flags=re.I | re.MULTILINE | re.DOTALL,
    ):
        sections.append((sec.group(1), sec.group(2), sec.start(2), sec.end(2)))
    return sections


_PARTICIPANTS_NAME = (
    r"(?:participants|subjects|controls|patients|volunteers|individuals"
    "|adults|children|adolescents|men|women|males|male|females|female)"
)


def _split_participants_section(
    section: str, section_start: int
) -> List[Tuple[str, int, int]]:
    parts = []
    start = 0
    for match in re.finditer(
        rf"(?:[^()]|\([^)]*\))*?{_PARTICIPANTS_NAME}(?:\s\([^)]*\))?",
        section,
        flags=re.I | re.DOTALL,
    ):
        parts.append(
            (
                section[start : match.end()],
                start + section_start,
                match.end() + section_start,
            )
        )
        start = match.end()
    return parts
