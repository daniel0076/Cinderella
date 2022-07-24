from abc import ABCMeta
from abc import abstractmethod


class DownloaderBase(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def verify_and_download(self):
        pass
