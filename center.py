from fastapi import FastAPI, responses
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
from object.Instance import Instance
from persistence.memoryPersistence import MemoryPersistence
from typing import Dict, Callable, Set
import uvicorn
from ConfigLoader import ConfigLoader
instances: Dict[str, Set[str]] = {}
unique: Dict[str, Instance] = {}
wsInstance: Dict[str, WebSocket] = {}
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
persistence = MemoryPersistence()
configLoader = ConfigLoader()


def login(instance: Instance, websocket: WebSocket) -> bool:
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


def logout(instance: Instance or str) -> bool:
    uid = str(instance)
    if uid not in unique:
        return False
    unique.pop(uid)
    instances[instance.serviceName].remove(uid)
    persistence.removeLog(uid)
    wsInstance.pop(uid)
    return True


async def log(instance: Instance, body: dict, websocket: WebSocket) -> None:
    uid = str(instance)
    # print(body["message"])
    await persistence.addLog(uid, body["message"])


async def route(instance: Instance, body: dict, websocket: WebSocket) -> None:
    result = instances.copy()
    for key in instances:
        result[key] = {}
        for uid in instances[key]:
            result[key][uid] = unique[uid].dict()
    payload = {
        "type": "route",
        "data": result
    }
    await websocket.send_json(payload)


async def config(instance: Instance, body: dict, websocket: WebSocket) -> None:
    payload = {
        "type": "config",
        "data": {}
    }
    if "config" in body and body["config"] is not None:
        payload["data"][body["config"]] = configLoader.config[body["config"]]
    else:
        payload["data"] = configLoader.config
    await websocket.send_json(payload)


wsCallable: Dict[str, Callable] = {
    "log": log,
    "route": route,
    "config": config
}


@app.websocket("/sws")
async def websocketEndpoint(websocket: WebSocket):
    try:
        instance = Instance(
            serviceName=websocket.headers.get("Service-Name"),
            hostname=websocket.headers.get("Hostname"),
            port=int(websocket.headers.get("Port"))
        )
        await websocket.accept()
        login(instance, websocket)
        while True:
            data = await websocket.receive_json()
            await wsCallable[data["type"]](instance, data, websocket)
    except WebSocketDisconnect:
        logout(instance)


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
    return responses.JSONResponse({"data": persistence.getLog(uid)})


@app.delete("/logout/{uid}")
async def deleteById(uid: str):
    return responses.JSONResponse({
        "message": "success" if logout(uid) else "failed"
    })


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=3100)
