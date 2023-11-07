from abc import ABC, abstractmethod
from typing import Dict,Union
class IRoute(ABC):
    @abstractmethod
    def doRoute(self):
        pass
    @abstractmethod
    def getRoute(self) -> Dict[str,Dict[str,Union[str,int]]]:
        pass

    @abstractmethod
    def getUrl(self, serviceName: str) -> str:
        pass
