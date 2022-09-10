from __future__ import annotations
import os
import hashlib
import re
import poplib
from email.message import Message
from email.parser import BytesParser
from email import policy
from typing import Union
from pathlib import Path

from downloaders.settings import MailSettings
from downloaders.base import DownloaderBase


class MailDownloader(DownloaderBase):
    """
    POP3 mail downloader
    """

    def __init__(self, settings: MailSettings):
        # create POP3 instance and login
        mailbox = poplib.POP3_SSL(settings.server, timeout=10)
        mailbox.user(settings.username)
        mailbox.pass_(settings.password)
        self.mailbox = mailbox
        self.settings = settings

    # builder pattern to ensure instance creation and encapsulate exceptions
    @staticmethod
    def create(settings: MailSettings) -> tuple[bool, Union[str, MailDownloader]]:
        try:
            mailbox = MailDownloader(settings)
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        print("MailDownloader initialized, configuration:")
        print("output directory: {}".format(mailbox.settings.output_directory))
        print("username: {}\n".format(mailbox.settings.username))
        return True, mailbox

    def run(self):
        num_mails = len(self.mailbox.list()[1])  # (response, ['line', ...], octets)
        print("Inbox: found {} mail(s)".format(num_mails))

        for i in range(num_mails):
            raw_email = b"\n".join(
                self.mailbox.retr(i + 1)[1]
            )  # retr()[1] means the octets
            mail = BytesParser(policy=policy.default).parsebytes(raw_email)
            self.verify_and_download(mail)

        self.mailbox.quit()

    def verify_and_download(self, mail: Message) -> bool:
        # for verification
        subject = mail["subject"]
        address = mail["from"].addresses[0]
        sender = "{}@{}".format(address.username, address.domain)

        # loop each source to check
        for source in self.settings.sources:
            if not source.enabled:
                continue

            # loop each possible statements in a source
            for statement in source.statements:
                # check the subject
                if not bool(re.search(statement.subject_keyword, subject)):
                    continue
                # mail found, verify sender for security concerns
                if statement.valid_senders and sender not in statement.valid_senders:
                    continue

                # looks good, download the attachment
                for attachment in mail.iter_attachments():
                    filename = attachment.get_filename()
                    # check if the filenames matchs the pattern in the settings
                    if not bool(re.search(statement.attachment_keyword, filename)):
                        continue

                    # process the attachment according to its content type
                    # https://datatracker.ietf.org/doc/html/rfc1341
                    transfer_encoding = attachment["Content-Transfer-Encoding"]

                    if transfer_encoding.lower() == "base64":
                        try:
                            bytes_content = attachment.get_content(
                                errors="strict"
                            ).encode()
                        except UnicodeDecodeError:
                            # at least try again with UTF-8
                            if attachment.get_content_charset().lower() != "utf-8":
                                attachment.set_charset("utf-8")
                                bytes_content = attachment.get_content().encode()

                    else:  # transfer_encoding == "binary" or "7bit"
                        bytes_content = attachment.get_content()

                    # append file hash to avoid collections
                    filehash = hashlib.sha256(bytes_content).hexdigest()
                    filename = "{}_{}".format(filehash[:8], filename)
                    output_directory = self.settings.output_directory.format(
                        statement_type=statement.type.value, source_name=source.name
                    )
                    save_to = Path(output_directory, filename)
                    if os.path.exists(save_to):
                        print(
                            "In mail: {}\nFile already downloaded: {}".format(
                                subject, filename
                            )
                        )
                        continue

                    # TODO: error handling
                    os.makedirs(save_to.parents[0], mode=0o755, exist_ok=True)
                    self._write(bytes_content, save_to)
                    print("In mail: {}\nDownloaded: {}".format(subject, filename))
                    return True

        return False

    def _write(self, content, save_to: Union[Path, str]) -> int:
        with open(save_to, "wb") as fp:
            return fp.write(content)
