import websocket
from object.serverConfig import ServerConfig
from object.instance import Instance
import json
from abc import abstractmethod
from threading import Thread


class Client:
    @abstractmethod
    async def log(self, data: str):
        pass


class WebSocketClient(Client):
    def __init__(self, serverConfig: ServerConfig, instance: Instance):
        headers = {
            "Service-Name": instance.serviceName,
            "Hostname": instance.hostname,
            "Port": str(instance.port)
        }
        self.ws = websocket.WebSocketApp(
            WebSocketClient.getServerUrl(serverConfig),
            headers,
            on_message=self._onMessage,
            on_error=self._onError,
            on_open=self._onOpen,
            on_close=self._onClose
        )
        self.ready = False
        self.cacheLog = ""
        self.thread = Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

    def run(self):
        self.ws.run_forever(reconnect=5)

    def getServerUrl(serverConfig: ServerConfig):
        return "ws://{}:{}/sws".format(
            serverConfig.host,
            serverConfig.port
        )

    def _onMessage(self, ws: websocket.WebSocketApp, message):
        return

    def _onError(self, ws: websocket.WebSocketApp, error):
        print(error)
        return

    def _onOpen(self, ws: websocket.WebSocketApp):
        self.ready = True
        return

    def _onClose(self, ws: websocket.WebSocketApp, close_status_code, close_msg):
        print("lost connection")
        self.ready = False
        return

    def log(self, data: str):
        self.cacheLog += data
        if not self.ready:
            return
        try:
            self.ws.send(json.dumps({
                "type": "log",
                "message": self.cacheLog
            }))
            self.cacheLog = ""
        except websocket.WebSocketConnectionClosedException:
            return
