import re
import dataclasses
import enum
from collections import defaultdict
from typing import Optional, Tuple, List, Sequence

from participants import _reading

_FEMALES_NAMES = r"\b(?:females?|women|woman|girls?)\b"
_MALES_NAMES = r"\b(?:males?|men|man|boys?)\b"


class ParticipantType(enum.Enum):
    HEALTHY = enum.auto()
    PATIENT = enum.auto()
    UNKNOWN = enum.auto()


@dataclasses.dataclass
class ParticipantsGroupInfo:
    name: str
    participant_type: ParticipantType
    count: int
    females_count: Optional[int]
    females_count: Optional[int]
    males_count: Optional[int]
    age_mean: Optional[float]
    age_range: Optional[Tuple[float]]
    mentions: List[_reading.DetailedParticipantsGroup]

    def __str__(self):
        details_parts = []
        if self.females_count is not None:
            details_parts.append(f"{self.females_count} females")
            details_parts.append(f"{self.males_count} males")
        if self.age_mean is not None:
            details_parts.append(f"mean age = {self.age_mean}")
        if self.age_range is not None:
            low, high = self.age_range
            details_parts.append(f"age range = {low} — {high}")
        details = ", ".join(details_parts)
        return f"{self.count} {self.name} ({details})"


@dataclasses.dataclass
class ParticipantsInfo:
    count: int
    females_count: Optional[int]
    males_count: Optional[int]
    age_mean: Optional[float]
    age_range: Optional[Tuple[float]]
    groups: List[ParticipantsGroupInfo]

    def __str__(self):
        return f"{self.count} participants: {list(map(str, self.groups))}"


def _group_by_section(
    extracted_groups: Sequence[_reading.DetailedParticipantsGroup],
):
    sections = defaultdict(list)
    for participant_group in extracted_groups:
        if participant_group.group_details:
            sections[participant_group.section_name].append(participant_group)
    return dict(sections)


def _get_type(participants_group: _reading.DetailedParticipantsGroup):
    if participants_group.group.name.value in ["hcs", "controls", "students"]:
        return ParticipantType.HEALTHY
    if (
        participants_group.group.adjective is not None
        and participants_group.group.adjective.value == "healthy"
    ):
        return ParticipantType.HEALTHY
    if participants_group.group.name.value in ["patients"]:
        return ParticipantType.PATIENT
    return ParticipantType.UNKNOWN


def _summarize_section(
    section_groups: Sequence[_reading.DetailedParticipantsGroup],
):
    participant_types = defaultdict(list)
    for group in section_groups:
        participant_types[_get_type(group)].append(group)
    if not participant_types:
        return None
    for groups in participant_types.values():
        if len(groups) > 1:
            return None
    if (
        ParticipantType.UNKNOWN in participant_types
        and len(participant_types) > 1
    ):
        return None
    return {k: v[0] for k, v in participant_types.items()}


def summarize(extracted_groups: Sequence[_reading.ParticipantsGroup]):
    if len(extracted_groups) == 1:
        kept_groups = {_get_type(extracted_groups[0]): extracted_groups[0]}
    else:
        sections = sorted(
            filter(
                bool,
                map(
                    _summarize_section,
                    _group_by_section(extracted_groups).values(),
                ),
            ),
            key=len,
        )
        if not sections:
            return None
        kept_groups = sections[-1]
    groups = []
    for group_type, group_mention in kept_groups.items():
        group_info = _summarize_participants_group(group_type, group_mention)
        groups.append(group_info)
    participants_info = _summarize_participants(groups)
    return participants_info


def _summarize_participants(groups):
    count = sum(g.count for g in groups)
    try:
        females_count = sum(g.females_count for g in groups)
    except TypeError:
        females_count = None
    try:
        males_count = sum(g.males_count for g in groups)
    except TypeError:
        males_count = None
    try:
        age_mean = sum(g.age_mean * g.count for g in groups) / sum(
            g.count for g in groups
        )
    except TypeError:
        age_mean = None
    try:
        age_min = min(g.age_range[0] for g in groups)
        age_max = max(g.age_range[1] for g in groups)
        age_range = (age_min, age_max)
    except TypeError:
        age_range = None
    return ParticipantsInfo(
        count, females_count, males_count, age_mean, age_range, groups
    )


def _summarize_participants_group(group_type, group_mention):
    info = defaultdict(list)
    for detail in group_mention.group_details:
        if isinstance(detail, _reading.ParticipantsSubGroup):
            if re.match(_FEMALES_NAMES, detail.name):
                info["females_counts"].append(detail.count)
            elif re.match(_MALES_NAMES, detail.name):
                info["males_counts"].append(detail.count)
        elif isinstance(detail, _reading.AgeMoments):
            info["age_means"].append(detail.mean)
        elif isinstance(detail, _reading.AgeRange):
            info["age_ranges"].append((detail.low, detail.high))
    females_count, males_count = None, None
    if "females_counts" in info:
        females_count = sum(info["females_counts"])
        if "males_counts" not in info:
            males_count = group_mention.group.count.value - females_count
    if "males_counts" in info:
        males_count = sum(info["males_counts"])
        if "females_counts" not in info:
            females_count = group_mention.group.count.value - males_count
    if (
        females_count is not None
        and females_count + males_count != group_mention.group.count.value
    ):
        females_count, males_count = None, None
    age_mean = None
    if "age_means" in info and len(info["age_means"]) == 1:
        age_mean = info["age_means"][0]
    age_range = None
    if "age_ranges" in info and len(info["age_ranges"]) == 1:
        age_range = info["age_ranges"][0]
    return ParticipantsGroupInfo(
        group_mention.group.name.value,
        group_type,
        group_mention.group.count.value,
        females_count,
        males_count,
        age_mean,
        age_range,
        [group_mention],
    )
