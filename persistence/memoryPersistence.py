from collections import deque
from pydantic import BaseModel
class MemoryPersistence(BaseModel):
    log:dict={}
    maxLogLength:int=2000
    async def addLog(self,uniqueId:str,message:str):
        buffer:deque=None
        if uniqueId not in self.log:
            buffer=self.log[uniqueId]=deque()
        else:
            buffer=self.log[uniqueId]
        if len(buffer) > self.maxLogLength:
            buffer.popleft()
        buffer.append(message)
    def getLog(self,uniqueId:str)->str:
        if uniqueId not in self.log:
            return ""
        return "".join(self.log[uniqueId])
    def removeLog(self,uniqueId:str):
        self.log.pop(uniqueId)