import argparse
import logging
import json
from downloaders.settings import DownloaderSettings
from downloaders.mail import MailDownloader

logging.basicConfig()  # note this will set logging globally to warning level
LOGGER = logging.getLogger("Downloader")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cinderella Pipeline - Statement Downloader"
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
    parser.add_argument(
        "--username", type=str, help="username, will override values in the config"
    )
    parser.add_argument(
        "--password", type=str, help="password, will override values in the config"
    )
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
    success, value = DownloaderSettings.from_dict(config_dict)
    if not success:
        LOGGER.error(value)
        exit(1)
    downloader_settings = value

    # create downloader object
    if downloader_settings.mail_settings:
        settings = downloader_settings.mail_settings

        # override configuration settings if commandline arguments are provided
        if args.username:
            settings.username = args.username
        if args.password:
            settings.password = args.password

        success, value = MailDownloader.create(settings)
        if not success:
            LOGGER.error(value)
            exit(1)

        mail_downloader = value
        mail_downloader.run()
