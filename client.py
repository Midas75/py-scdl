import aiohttp
from object.ServerConfig import ServerConfig
from object.Instance import Instance
from object.Task import Task, TaskType
from abc import ABC, abstractmethod
from threading import Thread
import asyncio
import queue
import time
from LogInterceptor import LogInterceptor
from ILog import ILog
from IRoute import IRoute
from IConfig import IConfig
import json
from typing import Dict, Union


class Client(ABC):
    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def getRoute(self):
        pass


class WebSocketClient(Client, ILog, IRoute, IConfig):
    def __init__(self, serverConfig: ServerConfig, instance: Instance, getConfigNow: bool = True):
        self.serverConfig = serverConfig
        self.instance = instance
        self.cacheLog = ""
        self.running = True
        self.thread = Thread(target=self._runLoop)
        self.queue = queue.Queue()
        self.thread.daemon = True
        self.thread.start()
        if getConfigNow:
            self._blockTillConfigLoaded()

    def _blockTillConfigLoaded(self):
        self.doConfig()
        while not hasattr(self, "config"):
            print("still not get config,sleep 3s")
            time.sleep(3)

    def _runLoop(self):
        self.loop = asyncio.new_event_loop()
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
                    await asyncio.gather(self._listen(), self._consume())
        except:
            print("Exception ocurred")

    async def _consume(self):
        while not self.ws.closed:
            task = None
            try:
                task = self.queue.get_nowait()
                if task.type == TaskType.LOG:
                    await self._log(task.data)
                elif task.type == TaskType.CLOSE:
                    await self._close()
                elif task.type == TaskType.ROUTE:
                    await self._route()
                elif task.type == TaskType.CONFIG:
                    await self._config(task.data)
            except:
                await asyncio.sleep(0.5)
                continue

    def getServerUrl(serverConfig: ServerConfig):
        return "ws://{}:{}/sws".format(serverConfig.host, serverConfig.port)

    async def _listen(self):
        while not self.ws.closed:
            try:
                msg = await self.ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    dataDict = json.loads(msg.data)
                    if dataDict["type"] == "route":
                        self.route = dataDict["data"]
                        print(json.dumps(self.route, indent=4))
                    elif dataDict["type"] == "config":
                        self.config = dataDict["data"]
                        print(json.dumps(self.config, indent=4))
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    await self.ws.close()
                    print("CLOSED")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("ERROR")
            except:
                continue
        print("listen loop exited")

    async def _log(self, data: str):
        self.cacheLog += data
        await self.ws.send_json({"type": "log", "message": self.cacheLog})
        self.cacheLog = ""

    async def _route(self):
        await self.ws.send_json({"type": "route"})

    async def _close(self):
        self.running = False
        await self.ws.close()

    async def _config(self, config: str = None):
        await self.ws.send_json({"type": "config", "config": config})

    def stop(self):
        self.queue.put_nowait(Task(TaskType.CLOSE))
        self.thread.join()

    def doLog(self, data: str):
        self.queue.put_nowait(Task(type=TaskType.LOG, data=data))

    def doRoute(self):
        self.queue.put_nowait(Task(type=TaskType.ROUTE))

    def getRoute(self) -> Dict[str, Dict[str, Union[str, int]]]:
        return self.route

    def getUrl(self, serviceName: str, withProtocol: bool = True) -> str:
        services = self.route[serviceName]
        key = next(iter(services))
        hostname = services[key]["hostname"]
        port = services[key]["port"]
        if withProtocol:
            return "http://{}:{}".format(hostname, port)
        else:
            return "{}:{}".format(hostname, port)

    def doConfig(self, firstKey: str = None):
        self.queue.put_nowait(Task(type=TaskType.CONFIG, data=firstKey))

    def getConfig(self) -> Dict[str, Dict]:
        return self.config

    def getConfigValueByKeyPath(self, keyPath: str, spliter: str = ".") -> Union[Dict, str]:
        if not hasattr(self, "config"):
            return None
        paths = keyPath.split(spliter)
        c = self.config
        for path in paths:
            if path in c and isinstance(c[path], Union[Dict, str]):
                c = c[path]
            else:
                return None
        return c


if __name__ == "__main__":
    serverConfig = ServerConfig(host="192.168.30.61", port=3100)
    instance = Instance(serviceName="all", hostname="192.168.30.61", port=3101)
    wsClient = WebSocketClient(serverConfig=serverConfig, instance=instance)
    li = LogInterceptor(wsClient)
    while True:
        # print(wsClient.getConfigValueByKeyPath("base"))
        time.sleep(3)
        # wsClient.doRoute()
        # wsClient.doConfig()
        print(time.strftime("%H:%M:%S"))
        # wsClient.doLog(time.strftime("%H:%M:%S") + "\n")
