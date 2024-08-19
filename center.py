from fastapi import FastAPI, responses
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
import os
import sys
from typing import Callable, Union, Any

sys.path.append(f"{os.path.dirname(__file__)}")
from base import Instance
from persistence import IPersistence, MemoryPersistence

import uvicorn
from config_loader import ConfigLoader

instances: dict[str, set[str]] = {}
unique: dict[str, Instance] = {}
wsInstance: dict[str, WebSocket] = {}
app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=f"{os.path.dirname(__file__)}/static"),
    name="static",
)
persistence: IPersistence = MemoryPersistence()
configLoader = ConfigLoader()


async def login(instance: Instance, websocket: WebSocket) -> bool:
    uid = str(instance)
    if uid in unique:
        return False
    unique[uid] = instance
    if instance.serviceName in instances:
        instances[instance.serviceName].add(uid)
    else:
        instances[instance.serviceName] = {uid}
    wsInstance[uid] = websocket
    return True


async def logout(instance: Union[Instance, str]) -> bool:
    uid = str(instance)
    if uid not in unique:
        return False
    unique.pop(uid)
    instances[instance.serviceName].remove(uid)
    await persistence.removeLog(uid)
    wsInstance.pop(uid)
    return True


async def log(instance: Instance, body: dict, websocket: WebSocket) -> None:
    uid = str(instance)
    await persistence.addLog(uid, body["message"])


async def route(instance: Instance, body: dict, websocket: WebSocket) -> None:
    result = instances.copy()
    for key in instances:
        result[key] = {}
        for uid in instances[key]:
            result[key][uid] = unique[uid].model_dump()
    payload = {"type": "route", "data": result}
    await websocket.send_json(payload)


async def config(instance: Instance, body: dict, websocket: WebSocket) -> None:
    payload = {"type": "config", "data": {}}
    if "config" in body and body["config"] is not None:
        payload["data"][body["config"]] = configLoader.config[body["config"]]
    else:
        payload["data"] = configLoader.config
    print(payload)
    await websocket.send_json(payload)


wsCallable: dict[str, Callable[[Instance, dict[str, Any, WebSocket]], None]] = {
    "log": log,
    "route": route,
    "config": config,
}


@app.websocket("/sws")
async def websocketEndpoint(websocket: WebSocket):
    try:
        instance = Instance(
            serviceName=websocket.headers.get("Service-Name"),
            hostname=websocket.headers.get("Hostname"),
            port=int(websocket.headers.get("Port")),
        )
        await websocket.accept()
        await login(instance, websocket)
        while True:
            data = await websocket.receive_json()
            await wsCallable[data["type"]](instance, data, websocket)
    except WebSocketDisconnect:
        await logout(instance)


@app.get("/config/reload")
async def reloadConfig():
    configLoader.loadConfig()
    return responses.JSONResponse({"msg": "ok"})


@app.post("/config/save/{firstKey}")
async def saveConfig(firstKey: str, reqeustBody: dict):
    configLoader.saveConfig(firstKey, reqeustBody)
    return responses.JSONResponse({"msg": "ok"})


@app.get("/config/list")
async def listConfig():
    return responses.JSONResponse({"data": list(configLoader.config.keys())})


@app.get("/config/get/{firstKey}")
async def getConfig(firstKey: str):
    if firstKey in configLoader.config:
        return responses.JSONResponse({"data": configLoader.config[firstKey]})
    else:
        return responses.JSONResponse({"data": "{}"})


@app.get("/list")
async def getList():
    return responses.JSONResponse({"data": list(unique.keys())})


@app.get("/log/{uid}")
async def getLog(uid: str):
    return responses.JSONResponse({"data":await persistence.getLog(uid)})


@app.delete("/logout/{uid}")
async def deleteById(uid: str):
    return responses.JSONResponse({"message": "success" if logout(uid) else "failed"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3100)
