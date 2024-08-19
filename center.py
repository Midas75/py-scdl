from fastapi import FastAPI, responses
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
import os
import sys
from typing import Callable, Union, Any
import uvicorn

sys.path.append(f"{os.path.dirname(__file__)}")
from base_model import Instance
from persistence import IPersistence, MemoryPersistence
from config_loader import ConfigLoader


class PySCDLCenter:
    def __init__(self, host: str = "0.0.0.0", port: int = 3100):
        self.instances = dict[str, set[str]]()
        self.unique = dict[str, Instance]()
        self.wsInstance = dict[str, WebSocket]()
        self.serverConfig = uvicorn.Config(app=FastAPI(),host=host,port=port)
        self.serverConfig.app.mount(
            "/static",
            StaticFiles(directory=f"{os.path.dirname(__file__)}/static"),
            name="static",
        )
        self.persistence: IPersistence = MemoryPersistence()
        self.configLoader = ConfigLoader()
        self.wsCallable: dict[
            str, Callable[[Instance, dict[str, Any, WebSocket]], None]
        ] = {
            "log": self.log,
            "route": self.route,
            "config": self.config,
        }

        @self.serverConfig.app.websocket("/sws")
        async def websocketEndpoint(websocket: WebSocket):
            try:
                instance = Instance(
                    serviceName=websocket.headers.get("Service-Name"),
                    hostname=websocket.headers.get("Hostname"),
                    port=int(websocket.headers.get("Port")),
                )
                await websocket.accept()
                await self.login(instance, websocket)
                while True:
                    data = await websocket.receive_json()
                    await self.wsCallable[data["type"]](instance, data, websocket)
            except WebSocketDisconnect:
                await self.logout(instance)

        @self.serverConfig.app.get("/config/reload")
        async def reloadConfig():
            self.configLoader.loadConfig()
            return responses.JSONResponse({"msg": "ok"})

        @self.serverConfig.app.post("/config/save/{firstKey}")
        async def saveConfig(firstKey: str, reqeustBody: dict):
            self.configLoader.saveConfig(firstKey, reqeustBody)
            return responses.JSONResponse({"msg": "ok"})

        @self.serverConfig.app.get("/config/list")
        async def listConfig():
            return responses.JSONResponse(
                {"data": list(self.configLoader.config.keys())}
            )

        @self.serverConfig.app.get("/config/get/{firstKey}")
        async def getConfig(firstKey: str):
            if firstKey in self.configLoader.config:
                return responses.JSONResponse(
                    {"data": self.configLoader.config[firstKey]}
                )
            else:
                return responses.JSONResponse({"data": "{}"})

        @self.serverConfig.app.get("/list")
        async def getList():
            return responses.JSONResponse({"data": list(self.unique.keys())})

        @self.serverConfig.app.get("/log/{uid}")
        async def getLog(uid: str):
            return responses.JSONResponse({"data": await self.persistence.getLog(uid)})

        @self.serverConfig.app.delete("/logout/{uid}")
        async def deleteById(uid: str):
            return responses.JSONResponse(
                {"message": "success" if self.logout(uid) else "failed"}
            )

    async def login(self, instance: Instance, websocket: WebSocket) -> bool:
        uid = str(instance)
        if uid in self.unique:
            return False
        self.unique[uid] = instance
        if instance.serviceName in self.instances:
            self.instances[instance.serviceName].add(uid)
        else:
            self.instances[instance.serviceName] = {uid}
        self.wsInstance[uid] = websocket
        return True

    async def logout(self, instance: Union[Instance, str]) -> bool:
        uid = str(instance)
        if uid not in self.unique:
            return False
        self.unique.pop(uid)
        self.instances[instance.serviceName].remove(uid)
        await self.persistence.removeLog(uid)
        self.wsInstance.pop(uid)
        return True

    async def log(self, instance: Instance, body: dict, websocket: WebSocket) -> None:
        uid = str(instance)
        await self.persistence.addLog(uid, body["message"])

    async def route(self, instance: Instance, body: dict, websocket: WebSocket) -> None:
        result = self.instances.copy()
        for key in self.instances:
            result[key] = {}
            for uid in self.instances[key]:
                result[key][uid] = self.unique[uid].model_dump()
        payload = {"type": "route", "data": result}
        await websocket.send_json(payload)

    async def config(
        self, instance: Instance, body: dict, websocket: WebSocket
    ) -> None:
        payload = {"type": "config", "data": {}}
        if "config" in body and body["config"] is not None:
            payload["data"][body["config"]] = self.configLoader.config[body["config"]]
        else:
            payload["data"] = self.configLoader.config
        await websocket.send_json(payload)


if __name__ == "__main__":
    uvicorn.Server(PySCDLCenter().serverConfig).run()
