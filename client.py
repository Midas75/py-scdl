import aiohttp
import os
import sys
from abc import ABC, abstractmethod
from threading import Thread, Event
import asyncio
import json
from typing import Union, Coroutine, Any, TextIO

import aiohttp.http_exceptions

sys.path.append(f"{os.path.dirname(__file__)}")
from base_model import ServerConfig, Instance


class ILog(ABC):
    @abstractmethod
    def doLog(self, data: str):
        raise NotImplementedError()


class IConfig(ABC):
    @abstractmethod
    def doConfig(self, firstKey: str):
        raise NotImplementedError()

    @abstractmethod
    def getConfig(self) -> dict[str, dict]:
        raise NotImplementedError()

    @abstractmethod
    def getConfigValueByKeyPath(self, keyPath: str):
        raise NotImplementedError()


class Client(ABC):
    @abstractmethod
    def stop(self):
        raise NotImplementedError()

    @abstractmethod
    def getRoute(self):
        raise NotImplementedError()


class IRoute(ABC):
    @abstractmethod
    def doRoute(self):
        raise NotImplementedError()

    @abstractmethod
    def getRoute(self) -> dict[str, dict[str, Union[str, int]]]:
        raise NotImplementedError()

    @abstractmethod
    def getUrl(self, serviceName: str) -> str:
        raise NotImplementedError()


class LogInterceptor:
    def __init__(self, target: ILog, original_stdout: TextIO = sys.stdout):
        self.original_stdout = original_stdout
        self.target = target
        sys.stdout = self

    def __del__(self):
        return self.stop()

    def stop(self) -> None:
        sys.stdout = self.original_stdout

    def write(self, message):
        self.target.doLog(message)
        return self.original_stdout.write(message)

    def flush(self) -> None:
        return self.original_stdout.flush()


class WebSocketClient(Client, ILog, IRoute, IConfig):
    eventQueue: asyncio.Queue[Coroutine]
    ws: aiohttp.ClientWebSocketResponse = None
    onConfigUpdatedEvent: Event
    onRouteUpdatedEvent: Event
    onLoopCreatedEvent: Event
    loop: asyncio.AbstractEventLoop
    session: aiohttp.ClientSession = None

    def __init__(
        self, serverConfig: ServerConfig, instance: Instance, getConfigNow: bool = True
    ):
        self.eventQueue = asyncio.Queue[Coroutine]()
        self.serverConfig = serverConfig
        self.instance = instance
        self.cacheLog = ""
        self.running = False
        self.thread = Thread(target=asyncio.run, args=[self._eventLoop()], daemon=True)
        self.onConfigUpdatedEvent = Event()
        self.onRouteUpdatedEvent = Event()
        self.onLoopCreatedEvent = Event()
        self.thread.start()
        self.onLoopCreatedEvent.wait()

        if getConfigNow:
            print("waiting for config load")
            self.onConfigUpdatedEvent.wait()

    async def _eventLoop(self):
        self.running = True
        self.loop = asyncio.get_event_loop()
        self.onLoopCreatedEvent.set()
        await self.eventQueue.put(self._connect())
        while self.running:
            cor = await self.eventQueue.get()
            asyncio.create_task(cor)

    async def _connect(self):
        if self.session != None:
            await self.session.close()
        if self.ws != None and not self.ws.closed:
            await self.ws.close()
        try:
            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(
                WebSocketClient.getServerUrl(self.serverConfig),
                headers={
                    "Service-Name": self.instance.serviceName,
                    "Hostname": self.instance.hostname,
                    "Port": str(self.instance.port),
                },
                autoclose=True,
            )
        except Exception as e:
            print(f"Exception ocurred in _connect:{e}, now sleep 10s and reconnect")
            await asyncio.sleep(10)
            await self.eventQueue.put(self._connect())
        else:
            await self.eventQueue.put(self._recv())
            self.doConfig()

    async def _recv(self):
        try:
            msg = await self.ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                dataDict = json.loads(msg.data)
                if dataDict["type"] == "route":
                    self.route = dataDict["data"]
                    if not self.onRouteUpdatedEvent.is_set():
                        self.onRouteUpdatedEvent.set()
                    print(json.dumps(self.route, indent=4))
                elif dataDict["type"] == "config":
                    self.config = dataDict["data"]
                    if not self.onConfigUpdatedEvent.is_set():
                        self.onConfigUpdatedEvent.set()
                    print(json.dumps(self.config, indent=4))
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise Exception("ERROR")
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                raise Exception("CLOSE")
            await self.eventQueue.put(self._recv())
        except Exception as e:
            print(f"Exception occurred in _recv:{e}")
            await self.eventQueue.put(self._connect())

    async def _log(self, data: str):
        self.cacheLog += data
        try:
            await self.ws.send_json({"type": "log", "message": self.cacheLog})
        except Exception as e:
            print(f"Exception occurred in _log:{e}")
        self.cacheLog = ""

    async def _route(self):
        await self.ws.send_json({"type": "route"})

    async def _close(self):
        self.running = False

    async def _config(self, firstKey: str = None):
        self.onConfigUpdatedEvent.clear()
        await self.ws.send_json({"type": "config", "config": firstKey})

    def stop(self):
        asyncio.run_coroutine_threadsafe(self.eventQueue.put(self._close()), self.loop)

    def doLog(self, data: str):
        asyncio.run_coroutine_threadsafe(
            self.eventQueue.put(self._log(data)), self.loop
        )

    def doRoute(self):
        self.onRouteUpdatedEvent.clear()
        asyncio.run_coroutine_threadsafe(self.eventQueue.put(self._route()), self.loop)

    def getRoute(
        self, waitForNew: bool = False
    ) -> dict[str, dict[str, Union[str, int]]]:
        if waitForNew:
            self.onRouteUpdatedEvent.wait()
        return self.route

    def getUrl(self, serviceName: str, withProtocol: bool = True) -> str:
        services = self.route[serviceName]
        key = next(iter(services))
        hostname = services[key]["hostname"]
        port = services[key]["port"]
        if withProtocol:
            return f"http://{hostname}:{port}"
        else:
            return f"{hostname}:{port}"

    def doConfig(self, firstKey: str = None):
        asyncio.run_coroutine_threadsafe(
            self.eventQueue.put(self._config(firstKey)), self.loop
        )

    def getConfig(self, waitForNew: bool = False) -> dict[str, dict]:
        if waitForNew:
            self.onConfigUpdatedEvent.wait()
        return self.config

    def getConfigValueByKeyPath(
        self, keyPath: str, spliter: str = "."
    ) -> Union[dict, str, Any, None]:
        if not hasattr(self, "config"):
            return None
        paths = keyPath.split(spliter)
        c = self.config
        for path in paths:
            if path in c:
                c = c[path]
            else:
                return None
        return c

    @staticmethod
    def getServerUrl(serverConfig: ServerConfig):
        return f"ws://{serverConfig.host}:{serverConfig.port}/sws"


if __name__ == "__main__":
    import time

    serverConfig = ServerConfig(host="127.0.0.1", port=3100)
    instance = Instance(serviceName="all", hostname="127.0.0.1", port=3101)
    c = WebSocketClient(serverConfig=serverConfig, instance=instance)
    li = LogInterceptor(c)
    while True:
        time.sleep(3)
        print(time.strftime("%H:%M:%S"))
