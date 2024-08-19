import sys
import os

sys.path.append(f"{os.path.dirname(__file__)}/..")
from client import WebSocketClient
from base_model import ServerConfig, Instance

c = WebSocketClient(
    serverConfig=ServerConfig(host="127.0.0.1", port=3100),
    instance=Instance(serviceName="test", hostname="127.0.0.1", port=8100),
)
input()
