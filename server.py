from fastapi import FastAPI, responses
from fastapi.staticfiles import StaticFiles
from object.instance import Instance
from object.logRequest import LogRequest
from persistence.memoryPersistence import MemoryPersistence
import sys
import uvicorn
instances = {}
unique = {}
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
persistence = MemoryPersistence()


@app.post("/login")
async def login(instance: Instance):
    print(instance)
    if str(instance) in unique:
        return responses.JSONResponse({"msg": "Already present"})
    unique[str(instance)] = instance
    if instance.serviceName in instances:
        instances[instance.serviceName].append(instance)
    else:
        instances[instance.serviceName] = [instance]
    return responses.JSONResponse({"msg": "success"})


@app.post("/log")
async def log(logRequest: LogRequest):
    if str(logRequest.instance) not in unique:
        return responses.JSONResponse({"msg": "Not in instances"})
    persistence.addLog(str(logRequest.instance), logRequest.message)
    return responses.JSONResponse({"msg": "success"})


@app.get("/list")
async def getList():
    return responses.JSONResponse({"data": list(unique.keys())})


@app.get("/log/{instanceId}")
async def getLog(instanceId: str):
    return responses.JSONResponse({"data": persistence.getLog(instanceId)})

@app.get("/service/{serviceName}")
async def getService(serviceName:str):
    return responses.JSONResponse({"data":instances[serviceName][0].dict()})

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=3100)
