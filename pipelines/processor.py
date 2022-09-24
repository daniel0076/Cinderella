import argparse
import logging
import json
from pathlib import Path
import sys
import os

processor_path = Path(__file__).parents[0] / "processors"
sys.path.append(processor_path.as_posix())
from processors.settings import ProcessorSettings  # noqa: E402
from processors.base import ProcessedResult  # noqa: E402
from processors.einvoice import Einvoice  # noqa: E402
from processors.richart import Richart  # noqa: E402
from processors.esun import ESun  # noqa: E402


logging.basicConfig()  # note this will set logging globally to warning level
LOGGER = logging.getLogger("Processor")

if __name__ == "__main__":
    # register the processors that we have
    processor_cls = {
        Einvoice.source_name: Einvoice,
        Richart.source_name: Richart,
        ESun.source_name: ESun,
    }

    parser = argparse.ArgumentParser(
        description="Cinderella Pipeline - raw file Processor"
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="path/to/config",
        required=True,
        help="path to config file",
    )
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)  # set debug globally
    elif args.verbose:
        LOGGER.setLevel(level=logging.INFO)

    # parse configuration
    LOGGER.info("Reading configuration from {}".format(args.config))

    with open(args.config, "r") as fp:
        config_dict = json.load(fp)

    # create configuration object
    success, value = ProcessorSettings.from_dict(config_dict)
    if not success:
        LOGGER.error(value)
        exit(1)
    settings = value

    # create processor objects according to config
    processor_objs = {}
    for src_settings in settings.sources:
        try:
            processor_objs[src_settings.name] = processor_cls[src_settings.name](
                settings.output_directory, settings.move_directory, src_settings
            )
            LOGGER.info(f"Creating {src_settings.name} object")
        except KeyError:
            LOGGER.warning(f"{src_settings.name} not yet implemented")
            continue

    print("Processor initialized, configuration:")
    print("input directory: {}".format(settings.input_directory))
    print("output directory: {}".format(settings.output_directory))
    print()

    input_dir = Path(settings.input_directory)
    for dirpath, _, filenames in os.walk(input_dir):
        files = [
            Path(dirpath, filename)
            for filename in filenames
            if not filename.startswith(".")
        ]

        for file in files:
            for source_name, processor in processor_objs.items():
                if source_name not in file.as_posix():
                    continue

                print(
                    f"\n{source_name}: processing {file.relative_to(settings.input_directory)}"
                )
                result: ProcessedResult = processor.process(file)
                if not result.success:
                    LOGGER.error(result.message)
