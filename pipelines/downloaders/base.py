from abc import ABC
from abc import abstractmethod


class DownloaderBase(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def verify_and_download(self):
        pass
