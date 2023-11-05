import aiohttp
from object.serverConfig import ServerConfig
from object.instance import Instance
from object.Task import Task, TaskType
from abc import ABC, abstractmethod
from threading import Thread
import asyncio
import queue
import time
from LogInterceptor import LogInterceptor
from ILog import ILog


class Client(ABC):
    @abstractmethod
    def stop(self):
        pass


class WebSocketClient(Client, ILog):
    def __init__(self, serverConfig: ServerConfig, instance: Instance):
        self.serverConfig = serverConfig
        self.instance = instance
        self.loop = asyncio.new_event_loop()
        self.cacheLog = ""
        self.running = True
        self.thread = Thread(target=self._runLoop)
        self.queue = queue.SimpleQueue()
        self.thread.daemon = True
        self.thread.start()

    def _runLoop(self):
        asyncio.set_event_loop(self.loop)
        while self.running:
            self.loop.run_until_complete(self._start())
            print("websocket exited,trying reconnecting after 10 seconds")
            time.sleep(10)

    async def _start(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    WebSocketClient.getServerUrl(self.serverConfig),
                    headers={
                        "Service-Name": self.instance.serviceName,
                        "Hostname": self.instance.hostname,
                        "Port": str(self.instance.port),
                    },
                ) as ws:
                    self.ws = ws
                    # await self._listen()
                    await self._consume()
                    # await asyncio.gather(self._listen(), self._consume())
        except:
            print("Exception ocurred")

    async def _consume(self):
        while not self.ws.closed:
            task = None
            try:
                task = self.queue.get()
            except:
                await asyncio.sleep(3)
                continue
            if task.type == TaskType.LOG:
                await self._log(task.data)
            elif task.type == TaskType.CLOSE:
                await self._close(task.data)
        print("consume loop exited")

    def getServerUrl(serverConfig: ServerConfig):
        return "ws://{}:{}/sws".format(serverConfig.host, serverConfig.port)

    async def _listen(self):
        print(self.ws.closed)
        while not self.ws.closed:
            try:
                print("waiting comming message")
                msg = await self.ws.receive()
                print("wait done")
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    self.ws.close()
                    print("CLOSED")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("ERROR")
            except:
                continue
        print("listen loop exited")

    async def _log(self, data: str):
        self.cacheLog += data
        try:
            print(self.ws.closed)
            await self.ws.send_json({"type": "log", "message": data})
            print(data)
            self.cacheLog = ""
        except:
            print("sending exception")
            return

    async def _close(self):
        try:
            self.running = False
            await self.ws.close()
        except:
            return

    def stop(self):
        self.queue.put(Task(TaskType.CLOSE))
        self.thread.join()

    def doLog(self, data: str):
        self.queue.put(Task(type=TaskType.LOG, data=data))


if __name__ == "__main__":
    serverConfig = ServerConfig(host="192.168.3.4", port=3100)
    instance = Instance(serviceName="all", hostname="192.168.3.4", port=3101)
    wsClient = WebSocketClient(serverConfig=serverConfig, instance=instance)
    # li = LogInterceptor(wsClient)
    while True:
        time.sleep(1)
        wsClient.doLog(time.strftime("%H:%M:%S") + "\n")
