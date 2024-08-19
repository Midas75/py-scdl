import os
import sys

sys.path.append(f"{os.path.dirname(__file__)}/..")
from . import base_model
from . import client

globalSCDLClient = None


def init(
    instanceServiceName: str,
    instanceHostname: str,
    instancePort: int,
    serverAddress: str,
    serverPort: int = 3100,
):
    global globalSCDLClient
    globalSCDLClient = client.WebSocketClient(
        base_model.ServerConfig(host=serverAddress, port=serverPort),
        base_model.Instance(
            serviceName=instanceServiceName,
            hostname=instanceHostname,
            port=instancePort,
        ),
    )
