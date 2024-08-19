from collections import deque


class IPersistence:
    async def addLog(self, uniqueId: str, message: str):
        raise NotImplementedError()

    async def getLog(self, uniqueId: str) -> str:
        raise NotImplementedError()

    async def removeLog(self, uniqueId: str):
        raise NotImplementedError()


class MemoryPersistence(IPersistence):
    def __init__(self, maxLogLength: int = 500) -> None:
        super().__init__()
        self.log = dict[str, deque[str]]()
        self.maxLogLength = maxLogLength

    async def addLog(self, uniqueId: str, message: str):
        if uniqueId not in self.log:
            self.log[uniqueId] = deque[str]()
        buffer = self.log[uniqueId]
        if len(buffer) > self.maxLogLength:
            buffer.popleft()
        buffer.append(message)

    async def getLog(self, uniqueId: str) -> str:
        if uniqueId not in self.log:
            return ""
        return "".join(self.log[uniqueId])

    async def removeLog(self, uniqueId: str):
        if uniqueId in self.log:
            del self.log[uniqueId]
