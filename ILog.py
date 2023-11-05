
from abc import ABC, abstractmethod
class ILog(ABC):
    @abstractmethod
    def doLog(self, data: str):
        pass