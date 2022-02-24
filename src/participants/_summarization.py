import dataclasses
import enum
from collections import defaultdict
from typing import Optional, Tuple, List, Sequence

from participants import _reading


@dataclasses.dataclass
class ParticipantsGroupInfo:
    name: str
    count: int
    females_count: Optional[int]
    females_count: Optional[int]
    males_count: Optional[int]
    age_mean: Optional[float]
    age_range: Optional[Tuple[float]]
    mentions: List[_reading.DetailedParticipantsGroup]


@dataclasses.dataclass
class ParticipantsInfo:
    total_count: int
    females_count: Optional[int]
    males_count: Optional[int]
    age_mean: Optional[float]
    age_range: Optional[Tuple[float]]
    groups: List[ParticipantsGroupInfo]


def _group_by_section(
    extracted_groups: Sequence[_reading.DetailedParticipantsGroup],
):
    sections = defaultdict(list)
    for participant_group in extracted_groups:
        if participant_group.group_details:
            sections[participant_group.section_name].append(participant_group)
    return sections


class ParticipantType(enum.Enum):
    HEALTHY = 1
    PATIENT = 2
    ANY = 3


def _get_type(participants_group: _reading.DetailedParticipantsGroup):
    if participants_group.group.name.value in ["hcs", "controls"]:
        return ParticipantType.HEALTHY
    if (
        participants_group.group.adjective is not None
        and participants_group.group.adjective.value == "healthy"
    ):
        return ParticipantType.HEALTHY
    if participants_group.group.name.value in ["patients"]:
        return ParticipantType.PATIENT
    return ParticipantType.ANY


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
    if ParticipantType.ANY in participant_types and len(participant_types) > 1:
        return None
    return participant_types


def summarize(extracted_groups: Sequence[_reading.ParticipantsGroup]):
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
    kept = sections[-1]
    groups = []
    for group_mention in kept.values():
        group_info = ParticipantsGroupInfo(
            group_mention[0].group.name,
            group_mention[0].group.count,
            0,
            0,
            0,
            (0, 0),
            group_mention,
        )
        groups.append(group_info)
    participants_info = ParticipantsInfo(
        sum(g.count.value for g in groups),
        sum(g.females_count for g in groups),
        sum(g.males_count for g in groups),
        0,
        (0, 0),
        groups,
    )
    return participants_info
