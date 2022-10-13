from pathlib import Path
import dataclasses
import re
from typing import List, Optional, Union, Tuple, Any, NewType

from lark import Lark, Transformer, Discard

DiscardType = Any

_MAX_LEN = 100
_MAX_LEN_DETAILS = 150

_PARTICIPANTS_SECTIONS = (
    r"(?:participants?|subjects?|patients|population|abstract)"
)
_PARTICIPANTS_NAME = (
    r"\b(?:participants|subjects|controls|hcs|patients|volunteers|individuals"
    r"|adults|children|adolescents|girls|boys|men|women|males"
    r"|male|females|female|students)\b"
)


def _get_parser(
    start: str, ambiguity: str, grammar: str = "participants_grammar"
) -> Lark:
    grammar = (
        Path(__file__)
        .parent.joinpath("_data", f"{grammar}.lark")
        .read_text("utf-8")
    )
    parser = Lark(
        grammar, start=start, ambiguity=ambiguity, g_regex_flags=re.I
    )
    return parser


def _get_n_participants_parser() -> Lark:
    return _get_parser(start="participants", ambiguity="explicit")


def _get_participants_details_parser() -> Lark:
    return _get_parser(start="participants_details", ambiguity="resolve")


@dataclasses.dataclass
class Node:
    pos_offset: int = dataclasses.field(repr=False)
    start_pos: int = dataclasses.field(repr=False)
    end_pos: int = dataclasses.field(repr=False)
    abs_start_pos: int = dataclasses.field(init=False)
    abs_end_pos: int = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.abs_start_pos = self.pos_offset + self.start_pos
        self.abs_end_pos = self.pos_offset + self.end_pos

    def description(self) -> str:
        return f"({self.abs_start_pos}, {self.abs_end_pos})"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.description()}>"


@dataclasses.dataclass
class Token(Node):
    raw_value: dataclasses.InitVar[str]
    value: str = dataclasses.field(init=False)

    def __post_init__(self, raw_value: str) -> None:  # type: ignore
        super().__post_init__()
        self.value = raw_value.lower()

    def description(self) -> str:
        return self.value


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
    adjectives: List[Adjective]
    name: ParticipantsName

    def description(self) -> str:
        adj = " ".join([a.value for a in self.adjectives])
        return f"{self.count.value} {adj} {self.name.value}"


@dataclasses.dataclass
class ParticipantsDetailsEntry(Node):
    pass


@dataclasses.dataclass
class ParticipantsSubGroup(ParticipantsDetailsEntry):
    count: int
    name: str

    def description(self) -> str:
        return f"{self.count} {self.name}"


@dataclasses.dataclass
class AgeMoments(ParticipantsDetailsEntry):
    mean: float
    std: Optional[float]

    def description(self) -> str:
        std_msg = f" ± {self.std}" if self.std is not None else ""
        return f"{self.mean}{std_msg}"


@dataclasses.dataclass
class AgeMedian(ParticipantsDetailsEntry):
    median: float

    def description(self) -> str:
        return f"{self.median}"


@dataclasses.dataclass
class AgeRange(ParticipantsDetailsEntry):
    low: float
    high: float

    def description(self) -> str:
        return f"{self.low} – {self.high}"


@dataclasses.dataclass
class ParticipantsDetails(Node):
    details: List[ParticipantsDetailsEntry]

    def description(self) -> str:
        return str(list(map(str, self.details)))


@dataclasses.dataclass
class DetailedParticipantsGroup(ParticipantsGroup):
    details: List[ParticipantsDetailsEntry]
    section_name: str

    def __init__(
        self,
        group: ParticipantsGroup,
        details: List[ParticipantsDetailsEntry],
        section_name: str,
    ) -> None:
        self.pos_offset = group.pos_offset
        self.start_pos = group.start_pos
        self.end_pos = group.end_pos
        self.abs_start_pos = group.abs_start_pos
        self.abs_end_pos = group.abs_end_pos
        self.count = group.count
        self.adjectives = group.adjectives
        self.name = group.name
        self.details = details
        self.section_name = section_name

    def description(self) -> str:
        group_descr = super().description()
        details_descr = ", ".join(map(str, self.details))
        return f"{group_descr} [{details_descr}]"


class ParticipantsTransformer(Transformer):
    def __init__(self, pos_offset, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pos_offset = pos_offset

    def participants_n(self, tree) -> ParticipantsGroup:
        *adj, name, count = tree
        if adj:
            start_pos = adj[0].start_pos
        else:
            start_pos = name.start_pos
        return ParticipantsGroup(
            self.pos_offset, start_pos, count.end_pos, count, adj, name
        )

    def participants_inline(self, tree) -> ParticipantsGroup:
        count, *adj, name = tree
        return ParticipantsGroup(
            self.pos_offset,
            count.start_pos,
            name.end_pos,
            count,
            adj,
            name,
        )

    def participants_details(self, tree) -> Optional[ParticipantsDetails]:
        if not tree:
            return None
        start_pos = min(child.start_pos for child in tree)
        end_pos = max(child.end_pos for child in tree)
        return ParticipantsDetails(self.pos_offset, start_pos, end_pos, tree)

    def participants_subgroup(self, tree) -> ParticipantsSubGroup:
        count, name = tree
        return ParticipantsSubGroup(
            self.pos_offset,
            count.start_pos,
            name.end_pos,
            count.value,
            name.value,
        )

    def age_mean_std(self, tree) -> AgeMoments:
        mean, std = tree
        return AgeMoments(
            self.pos_offset,
            mean.start_pos,
            std.end_pos,
            float(mean.value),
            float(std.value),
        )

    def age_mean(self, tree) -> AgeMoments:
        (mean,) = tree
        return AgeMoments(
            self.pos_offset,
            mean.start_pos,
            mean.end_pos,
            float(mean.value),
            None,
        )

    def age_median(self, tree) -> AgeMedian:
        (median,) = tree
        return AgeMedian(
            self.pos_offset,
            median.start_pos,
            median.end_pos,
            float(median.value),
        )

    def age_range(self, tree) -> AgeRange:
        low, high = tree
        return AgeRange(
            self.pos_offset,
            low.start_pos,
            high.end_pos,
            float(low.value),
            float(high.value),
        )

    def extra_participants_detail(self, tree) -> DiscardType:
        return Discard

    def n_value(self, tree) -> NValue:
        lp, n, rp = tree
        return NValue(self.pos_offset, lp.start_pos, rp.end_pos, n.value)

    def number(self, tree) -> Number:
        return Number(
            self.pos_offset, tree[0].start_pos, tree[0].end_pos, tree[0].value
        )

    def hundred_text_number(self, tree) -> Number:
        hundred_part, rest = tree
        if rest is None:
            value = 100 * hundred_part.value
            end_pos = hundred_part.end_pos
        else:
            value = 100 * hundred_part.value + rest.value
            end_pos = rest.end_pos
        return Number(self.pos_offset, hundred_part.start_pos, end_pos, value)

    def dozen_text_number(self, tree) -> Number:
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

    def UNIT_NAME(self, tree) -> Number:
        value = (
            "zero one two three four five six seven eight nine".split().index(
                tree.value.lower()
            )
        )
        return Number(
            self.pos_offset, tree.start_pos, tree.end_pos, int(value)
        )

    def TEEN_NAME(self, tree) -> Number:
        value = (
            "ten eleven twelve thirteen fourteen fifteen sixteen "
            "seventeen eighteen nineteen".split().index(tree.value.lower())
            + 10
        )
        return Number(self.pos_offset, tree.start_pos, tree.end_pos, value)

    def DOZEN_NAME(self, tree) -> Number:
        value = (
            "zero ten twenty thirty forty fifty sixty "
            "seventy eighty ninety".split().index(tree.value.lower())
        ) * 10
        return Number(self.pos_offset, tree.start_pos, tree.end_pos, value)

    def INT(self, tree) -> Number:
        return Number(
            self.pos_offset, tree.start_pos, tree.end_pos, int(tree.value)
        )

    def PARTICIPANTS_NAME(self, tree) -> ParticipantsName:
        return ParticipantsName(
            self.pos_offset, tree.start_pos, tree.end_pos, tree.value
        )

    def ADJ(self, tree) -> Adjective:
        return Adjective(
            self.pos_offset, tree.start_pos, tree.end_pos, tree.value
        )


def resolve_n_participants(transformed_text) -> ParticipantsGroup:
    if not hasattr(transformed_text, "children"):
        return transformed_text
    return sorted(
        map(resolve_n_participants, transformed_text.children),
        key=lambda c: (-c.count.end_pos, c.count.start_pos),
    )[0]


class Reader:
    def __init__(self) -> None:
        self._participants_parser = _get_n_participants_parser()
        self._details_parser = _get_participants_details_parser()

    def extract_details(
        self, text: str, start_pos: int, end_pos: int
    ) -> List[ParticipantsDetailsEntry]:
        all_extracted = []
        end_pos = min(end_pos, start_pos + _MAX_LEN_DETAILS)
        for match in re.finditer(r"(\([^)]+\))", text[start_pos:end_pos]):
            transformer = ParticipantsTransformer(start_pos + match.start(1))
            try:
                extracted = transformer.transform(
                    self._details_parser.parse(match.group(1))
                )
            except Exception:
                extracted = []
            if extracted:
                all_extracted.extend(extracted.details)
        return all_extracted

    def extract_from_text(self, text: str) -> List[DetailedParticipantsGroup]:
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
                        extracted_from_section[i],
                        details,
                        section_name=section_name,
                    )
                )
            if extracted_from_section:
                details = self.extract_details(
                    text, extracted_from_section[-1].abs_start_pos, section_end
                )
                detailed.append(
                    DetailedParticipantsGroup(
                        extracted_from_section[-1],
                        details,
                        section_name=section_name,
                    )
                )

            result.extend(detailed)
        return result


def _get_participants_sections(
    article_text: str,
) -> List[Tuple[str, str, int, int]]:
    sections: List[Tuple[str, str, int, int]] = []
    start = 0
    sec_pat = re.compile(
        rf"^(#+) (.*{_PARTICIPANTS_SECTIONS}.*)$", flags=re.I | re.MULTILINE
    )
    while start < len(article_text):
        sec_head = sec_pat.search(article_text, start)
        if sec_head is None:
            return sections
        level = len(sec_head.group(1))
        next_sec_pat = re.compile(
            rf"^#{{1,{level}}} ", flags=re.I | re.MULTILINE
        )
        start = sec_head.end()
        next_sec = next_sec_pat.search(article_text, start)
        if next_sec is None:
            end = len(article_text)
        else:
            end = next_sec.start()
        sections.append(
            (sec_head.group(2).strip(), article_text[start:end], start, end)
        )
        start = end
    return sections


def _finditer(pattern: re.Pattern, string: str):
    start = 0
    while start < len(string):
        match = pattern.match(string, start)
        if match is None:
            return
        yield match
        start = match.end()


def _split_participants_section(
    section: str, section_start: int
) -> List[Tuple[str, int, int]]:
    parts = []
    pattern = re.compile(
        rf"(?:[^(]|\([^)]*\))*?({_PARTICIPANTS_NAME})(?:\s\([^)]*\))?",
        flags=re.I | re.DOTALL,
    )
    for match in _finditer(
        pattern,
        section,
    ):
        start = match.start()
        found = section[start : match.end(1)]
        imatch = re.match(
            rf"^(?:[^(]|\([^)]*\))*?(.{{,{_MAX_LEN}}})$",
            found,
            flags=re.I | re.DOTALL,
        )
        if imatch is not None:
            start += imatch.start(1)
        else:
            start = max(start, match.end() - _MAX_LEN)
        parts.append(
            (
                section[start : match.end()],
                start + section_start,
                match.end() + section_start,
            )
        )
    return parts
