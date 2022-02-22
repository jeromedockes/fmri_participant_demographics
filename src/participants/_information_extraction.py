from pathlib import Path
import dataclasses
import re
from typing import List, Optional, Union, Tuple

from lark import Lark, Transformer, Discard


def _get_parser(start, ambiguity) -> Lark:
    grammar = (
        Path(__file__)
        .parent.joinpath("_data", "participants_grammar.lark")
        .read_text("utf-8")
    )
    parser = Lark(
        grammar, start=start, ambiguity=ambiguity, g_regex_flags=re.I
    )
    return parser


def _get_n_participants_parser():
    return _get_parser(start="participants", ambiguity="explicit")


def _get_participants_details_parser():
    return _get_parser(start="participants_details", ambiguity="resolve")


@dataclasses.dataclass
class Node:
    pos_offset: int = dataclasses.field(repr=False)
    start_pos: int = dataclasses.field(repr=False)
    end_pos: int = dataclasses.field(repr=False)
    abs_start_pos: int = dataclasses.field(init=False)
    abs_end_pos: int = dataclasses.field(init=False)

    def __post_init__(self):
        self.abs_start_pos = self.pos_offset + self.start_pos
        self.abs_end_pos = self.pos_offset + self.end_pos


@dataclasses.dataclass
class Token(Node):
    raw_value: dataclasses.InitVar[str]
    value: str = dataclasses.field(init=False)

    def __post_init__(self, raw_value):
        self.value = raw_value.lower()


@dataclasses.dataclass
class Adjective(Token):
    pass


@dataclasses.dataclass
class ParticipantsName(Token):
    pass


@dataclasses.dataclass
class Number(Node):
    value: int


@dataclasses.dataclass
class NValue(Number):
    pass


@dataclasses.dataclass
class ParticipantsGroup(Node):
    count: Number
    adjective: Optional[Adjective]
    name: ParticipantsName

    def __str__(self):
        adj = f"{self.adjective.value} " if self.adjective is not None else ""
        return (
            f"{self.__class__.__name__}: "
            f"{self.count.value} {adj}{self.name.value}"
        )


@dataclasses.dataclass
class ParticipantsSubGroup(Node):
    count: Number
    name: ParticipantsName

    def __str__(self):
        return f"{self.__class__.__name__}: {self.count} {self.name}"


@dataclasses.dataclass
class AgeMoments(Node):
    mean: float
    std: Optional[float]

    def __str__(self):
        std_msg = f" ± {self.std}" if self.std is not None else ""
        return f"{self.__class__.__name__}: {self.mean}{std_msg}"


@dataclasses.dataclass
class AgeRange(Node):
    low: float
    high: float

    def __str__(self):
        return f"{self.__class__.__name__}: {self.low} – {self.high}"


@dataclasses.dataclass
class ParticipantsDetails(Node):
    details: List[Union[ParticipantsSubGroup, AgeMoments, AgeRange]]

    def __str__(self):
        content = str(list(map(str, self.details)))
        return f"{self.__class__.__name__}: {content}"


class DetailedParticipantsGroup:
    def __init__(self, group, group_details):
        self.group = group
        self.group_details = group_details

    def __str__(self):
        details = ", ".join(map(str, self.group_details))
        return f"{self.group} [{details}]"


class ParticipantsTransformer(Transformer):
    def __init__(self, pos_offset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pos_offset = pos_offset

    def participants_n(self, tree):
        if len(tree) == 2:
            name, count = tree
            adj = None
            start_pos = name.start_pos
        else:
            adj, name, count = tree
            start_pos = adj.start_pos
        return ParticipantsGroup(
            self.pos_offset, start_pos, count.end_pos, count, adj, name
        )

    def participants_inline(self, tree):
        if len(tree) == 2:
            count, name = tree
            adj = None
        else:
            count, adj, name = tree
        return ParticipantsGroup(
            self.pos_offset,
            count.start_pos,
            name.end_pos,
            count,
            adj,
            name,
        )

    def participants_details(self, tree):
        if not tree:
            return None
        start_pos = min(child.start_pos for child in tree)
        end_pos = max(child.end_pos for child in tree)
        return ParticipantsDetails(self.pos_offset, start_pos, end_pos, tree)

    def participants_subgroup(self, tree):
        count, name = tree
        return ParticipantsSubGroup(
            self.pos_offset,
            count.start_pos,
            name.end_pos,
            count.value,
            name.value,
        )

    def age_mean_std(self, tree):
        mean, std = tree
        return AgeMoments(
            self.pos_offset,
            mean.start_pos,
            std.end_pos,
            float(mean.value),
            float(std.value),
        )

    def age_mean(self, tree):
        (mean,) = tree
        return AgeMoments(
            self.pos_offset,
            mean.start_pos,
            mean.end_pos,
            float(mean.value),
            None,
        )

    def age_range(self, tree):
        low, high = tree
        return AgeRange(
            self.pos_offset,
            low.start_pos,
            high.end_pos,
            float(low.value),
            float(high.value),
        )

    def extra_participants_detail(self, tree):
        return Discard

    def n_value(self, tree):
        lp, n, rp = tree
        return NValue(self.pos_offset, lp.start_pos, rp.end_pos, n.value)

    def hundred_text_number(self, tree):
        hundred_part, rest = tree
        if rest is None:
            value = 100 * hundred_part.value
            end_pos = hundred_part.end_pos
        else:
            value = 100 * hundred_part.value + rest.value
            end_pos = rest.end_pos
        return Number(self.pos_offset, hundred_part.start_pos, end_pos, value)

    def dozen_text_number(self, tree):
        if len(tree) == 1:
            teen = tree[0]
            return teen
        dozen, unit = tree
        if unit is None:
            value = dozen.value
            end_pos = dozen.end_pos
        else:
            value = dozen.value + unit.value
            end_pos = unit.end_pos
        return Number(self.pos_offset, dozen.start_pos, end_pos, value)

    def UNIT_NAME(self, tree):
        value = (
            "zero one two three four five six seven eight nine".split().index(
                tree.value.lower()
            )
        )
        return Number(
            self.pos_offset, tree.start_pos, tree.end_pos, int(value)
        )

    def TEEN_NAME(self, tree):
        value = (
            "ten eleven twelve thirteen fourteen fifteen sixteen "
            "seventeen eighteen nineteen".split().index(tree.value.lower())
            + 10
        )
        return Number(self.pos_offset, tree.start_pos, tree.end_pos, value)

    def DOZEN_NAME(self, tree):
        value = (
            "zero ten twenty thirty fourty fifty sixty "
            "seventy eighty ninety".split().index(tree.value.lower())
        ) * 10
        return Number(self.pos_offset, tree.start_pos, tree.end_pos, value)

    def INT(self, tree):
        return Number(
            self.pos_offset, tree.start_pos, tree.end_pos, int(tree.value)
        )

    def PARTICIPANTS_NAME(self, tree):
        return ParticipantsName(
            self.pos_offset, tree.start_pos, tree.end_pos, tree.value
        )

    def ADJ(self, tree):
        return Adjective(
            self.pos_offset, tree.start_pos, tree.end_pos, tree.value
        )


def resolve_n_participants(transformed_text):
    if not hasattr(transformed_text, "children"):
        return transformed_text
    return sorted(
        map(resolve_n_participants, transformed_text.children),
        key=lambda c: (-c.count.end_pos, c.count.start_pos),
    )[0]


class Extractor:
    def __init__(self):
        self._participants_parser = _get_n_participants_parser()
        self._details_parser = _get_participants_details_parser()

    def extract_details(self, text, start_pos, end_pos):
        all_extracted = []
        for match in re.finditer(r"(\([^)]+\))", text[start_pos:end_pos]):
            transformer = ParticipantsTransformer(start_pos + match.start(1))
            extracted = transformer.transform(
                self._details_parser.parse(match.group(1))
            )
            if extracted:
                all_extracted.extend(extracted.details)
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
                transformer = ParticipantsTransformer(part_start)
                try:
                    extracted = resolve_n_participants(
                        transformer.transform(
                            self._participants_parser.parse(part)
                        )
                    )
                except Exception:
                    pass
                else:
                    extracted_from_section.append(extracted)
            detailed = []
            for i in range(len(extracted_from_section) - 1):
                details = self.extract_details(
                    text,
                    extracted_from_section[i].abs_start_pos,
                    extracted_from_section[i + 1].abs_end_pos,
                )
                detailed.append(
                    DetailedParticipantsGroup(
                        extracted_from_section[i], details
                    )
                )
            if extracted_from_section:
                details = self.extract_details(
                    text, extracted_from_section[-1].abs_start_pos, section_end
                )
                detailed.append(
                    DetailedParticipantsGroup(
                        extracted_from_section[-1], details
                    )
                )

            result.extend(detailed)
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
