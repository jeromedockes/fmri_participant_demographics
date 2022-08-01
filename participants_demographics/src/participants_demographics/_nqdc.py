from pathlib import Path

from participants_demographics import _information_extraction

_STEP_NAME = "extract_participants_demographics"
_STEP_DESCRIPTION = (
    "Extract participants count, sex and age from studies' text."
)


def extract_from_nqdc_data(extracted_data_dir, output_dir=None):
    extracted_data_dir = Path(extracted_data_dir)
    if output_dir is None:
        output_dir = extracted_data_dir.with_name(
            extracted_data_dir.name.replace(
                "_extractedData", "_participantsDemographics"
            )
        )
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    _information_extraction.extract_from_dataset(
        extracted_data_dir.joinpath("text.csv"),
        output_dir.joinpath("demographics.jsonl"),
    )
    return output_dir, 0


class DemographicsStep:
    name = _STEP_NAME
    short_description = _STEP_DESCRIPTION

    def edit_argument_parser(self, argument_parser) -> None:
        argument_parser.add_argument(
            "--demographics",
            action="store_true",
            help="Extract demographic information about "
            "each study's participants.",
        )

    def run(self, args, previous_steps_output):
        if not args.demographics:
            return None, 0
        return extract_from_nqdc_data(previous_steps_output["extract_data"])


class DemographicsCommand:
    name = _STEP_NAME
    short_description = _STEP_DESCRIPTION

    def edit_argument_parser(self, argument_parser) -> None:
        argument_parser.add_argument(
            "extracted_data_dir",
            help="Directory containing extracted data CSV files."
            "It is a directory created by nqdc whose name ends "
            "with 'extractedData'.",
        )

    def run(self, args):
        return extract_from_nqdc_data(args.extracted_data_dir)[1]


def get_nqdc_actions():
    return {
        "pipeline_steps": [DemographicsStep()],
        "commands": [DemographicsCommand()],
    }
