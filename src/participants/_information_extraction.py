from pathlib import Path
import re
from typing import List

from lark import Lark, Transformer


def _get_parser() -> Lark:
    grammar = (
        Path(__file__)
        .parent.joinpath("_data", "n_participants_grammar.lark")
        .read_text("utf-8")
    )
    parser = Lark(grammar, start="participants", ambiguity="explicit")
    return parser


class ParticipantsTransformer(Transformer):
    def INT(self, n):
        return int(n)

    def digit_number(self, n):
        return int(n[0])

    def UNIT_NAME(self, n):
        return (
            "zero one two three four five six seven eight nine".split().index(
                str(n)
            )
        )

    def unit_text_number(self, n):
        return n[0]

    def unit_part(self, n):
        return n[0]

    def DOZEN_NAME(self, n):
        return (
            "zero ten twenty thirty fourty fifty sixty "
            "seventy eighty ninety".split().index(str(n))
        ) * 10

    def TEEN_NAME(self, n):
        return (
            "ten eleven twelve thirteen fourteen fifteen sixteen "
            "seventeen eighteen nineteen".split().index(str(n)) + 10
        )

    def dozen_text_number(self, n):
        return sum(p for p in n if p is not None)

    def dozen_part(self, n):
        return n[0]

    def hundred_part(self, n):
        return 100 * n[0]

    def hundred_text_number(self, n):
        return sum(p for p in n if p is not None)

    def text_number(self, n):
        return n[0]

    def participants_desc(self, desc):
        return desc[-1]

    def PARTICIPANTS_NAME(self, name):
        return str(name)

    def participants_inline(self, part):
        return {"n_participants": part[1], "participants_name": part[2]}

    def participants_n(self, part):
        return {"n_participants": part[1], "participants_name": part[0]}

    def participants(self, part):
        return part[0]

    def extra_text(self, extra):
        return " ".join(extra)


class Extractor:
    def __init__(self):
        self._parser = _get_parser()
        self._transformer = ParticipantsTransformer()

    def extract(self, text):
        tree = self._parser.parse(text.lower())
        transformed = self._transformer.transform(tree)
        if hasattr(transformed, "children"):
            return transformed.children[0]
        return transformed


def _get_participants_sections(article_text: str) -> List[str]:
    sections = re.findall(
        r"^#[^\n]*(participants?|subjects?|abstract)[^\n]*(.*?)(?:\n\n\n|^#)",
        article_text,
        flags=re.I | re.MULTILINE | re.DOTALL,
    )
    return sections


_PARTICIPANTS_NAME = (
    r"(participants|subjects|controls|patients|volunteers|individuals"
    "|adults|children|adolescents|men|women|males|male|females|female)"
)


def _split_participants_section(section: str) -> List[str]:
    all_parts = re.split(_PARTICIPANTS_NAME, section, flags=re.I)
    concatenated_parts = []
    for idx in range(1, len(all_parts) - 1, 2):
        concatenated_parts.append(all_parts[idx - 1] + all_parts[idx])
        concatenated_parts.append(all_parts[idx] + all_parts[idx + 1])
    return concatenated_parts
