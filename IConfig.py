from abc import ABC, abstractmethod
from typing import Dict


class IConfig(ABC):
    @abstractmethod
    def doConfig(self,firstKey:str):
        pass

    @abstractmethod
    def getConfig(self) -> Dict[str, Dict]:
        pass

    @abstractmethod
    def getConfigValueByKeyPath(self,keyPath:str):
        pass
