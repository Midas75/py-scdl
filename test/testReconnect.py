import sys
import os
import threading
import uvicorn
import time

sys.path.append(f"{os.path.dirname(__file__)}/..")
from client import WebSocketClient
from base_model import ServerConfig, Instance
from center import PySCDLCenter

center = PySCDLCenter()


def createAThread() -> uvicorn.Server:
    server = uvicorn.Server(center.serverConfig)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server


s = createAThread()
c = WebSocketClient(
    serverConfig=ServerConfig(host="127.0.0.1", port=3100),
    instance=Instance(serviceName="test", hostname="127.0.0.1", port=8100),
)
while True:
    input("press any key to restart server")
    s.handle_exit(None, None)
    time.sleep(2)
    s = createAThread()
