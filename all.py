from LogInterceptor import LogInterceptor
from object.instance import Instance
from object.serverConfig import ServerConfig
from client import WebSocketClient
import time
if __name__ == "__main__":
    sc = ServerConfig(host="192.168.30.61")
    instance = Instance(serviceName="all", hostname="192.168.30.61", port=3101)
    wsClient = WebSocketClient(sc, instance)
    # li = LogInterceptor(wsClient)
    while True:
        current_time = time.strftime("%H:%M:%S")
        await wsClient.log(current_time)
        time.sleep(5)
