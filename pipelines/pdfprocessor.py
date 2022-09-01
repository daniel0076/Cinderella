import argparse
import logging
import json
from pathlib import Path
import sys
import os
from datatypes import AfterProcessedAction

processor_path = Path(__file__).parents[0] / "pdfprocessors"
sys.path.append(processor_path.as_posix())
from pdfprocessors.settings import PDFProcessorSettings, StatementSettings
from pdfprocessors.koko import KokoPDFProcessor
from pdfprocessors.base import ProcessedResult


logging.basicConfig()  # note this will set logging globally to warning level
LOGGER = logging.getLogger("PDFProcessor")

if __name__ == "__main__":
    processor_cls = {
        KokoPDFProcessor.identifier: KokoPDFProcessor
    }

    parser = argparse.ArgumentParser(
        description="Cinderella Pipeline - PDF to CSV Processor"
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
    success, value = PDFProcessorSettings.from_dict(config_dict)
    if not success:
        LOGGER.error(value)
        exit(1)
    settings = value

    # create pdfprocessor objects
    processor_objs = {}
    for src_settings in settings.sources:
        try:
            processor_objs[src_settings.identifier] = processor_cls[src_settings.identifier](src_settings)
        except IndexError:
            LOGGER.warning(f"{src_settings.identifier} not yet implemented")
            continue

    input_dir = Path(settings.input_directory)
    for dirpath, _, filenames in os.walk(input_dir):
        files = [Path(dirpath, filename) for filename in filenames if not filename.startswith(".")]

        for file in files:
            for identifier, processor in processor_objs.items():
                if identifier not in file.as_posix():
                    continue

                result: ProcessedResult = processor.process(file)
                if not result.success:
                    continue

                filename = result.date.strftime("%Y%m") + ".csv"
                output_directory = Path(settings.output_directory.format(
                    identifier=identifier, statement_type=result.type.value))
                output_path = output_directory / filename
                # ensure the directory is created
                os.makedirs(output_directory, exist_ok=True)
                result.data.to_csv(output_path, header=False, index=False)

                # execute action after processed
                stmt_settings: StatementSettings = processor.get_settings(result.type)

                if stmt_settings.after_processed == AfterProcessedAction.move:
                    dst_directory = Path(settings.move_directory.format(
                        identifier=identifier, statement_type=result.type.value))
                    dst = dst_directory / file.name
                    os.makedirs(dst_directory, exist_ok=True)
                    os.rename(file, dst)
                elif stmt_settings.after_processed == AfterProcessedAction.delete:
                    os.remove(file)
                elif stmt_settings.after_processed == AfterProcessedAction.keep:
                    pass


