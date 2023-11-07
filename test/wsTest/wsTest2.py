import aiohttp
import queue
from threading import Thread
import asyncio
import time


class WebSocketClient():
    def __init__(self):
        self.cacheLog = ""
        self.running = True
        self.thread = Thread(target=self._runLoop)
        self.queue = queue.SimpleQueue()
        self.thread.daemon = True
        self.thread.start()

    def _runLoop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        while self.running:
            print("before loop run")
            self.loop.run_until_complete(self._start())
            print("websocket exited,trying reconnecting after 10 seconds")
            time.sleep(10)

    async def _start(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    "ws://192.168.30.61:3100/sws",
                    headers={
                        "Service-Name": "all",
                        "Hostname": "192.168.30.61",
                        "Port": str(3101),
                    },
                ) as ws:
                    self.ws = ws
                    # await self._consume()
                    await asyncio.gather(self._listen(), self._consume())
        except:
            print("Exception ocurred")

    async def _consume(self):
        while not self.ws.closed:
            task = None
            try:
                task = self.queue.get_nowait()
            except:
                await asyncio.sleep(0.1)
                continue
            if task["type"] == 0:
                await self._log(task["data"])
            elif task["type"] == 1:
                await self._close(task["data"])
        print("consume loop exited")
        # while True:
        #     if self.queue.empty():
        #         await asyncio.sleep(3)
        #     else:
        #         msg = self.queue.get()
        #         if msg is not None:
        #             await self._log(msg["data"])
        #             # await self.ws.send_json({"type": "log", "message": msg["data"]})

    async def _listen(self):
        while not self.ws.closed:
            # try:
            print("waiting comming message")
            msg = await self.ws.receive()
            print("wait done")
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                self.ws.close()
                print("CLOSED")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("ERROR")
            # except:
            #     print("Exception ocurred")
            #     continue
        print("listen loop exited")

    async def _log(self, data: str):
        # self.cacheLog += data
        try:
            print(data)
            await self.ws.send_json({"type": "log", "message": data})
            self.cacheLog = ""
        except:
            print("sending exception")
            return

    async def _close(self, ws):
        try:
            self.running = False
            await ws.close()
        except:
            return

    def stop(self):
        self.queue.put({"type": 1})
        self.thread.join()

    def doLog(self, data: str):
        self.queue.put_nowait({"type": 0, "data": data})


if __name__ == "__main__":
    wsClient = WebSocketClient()
    # li = LogInterceptor(wsClient)
    while True:
        time.sleep(1)
        wsClient.doLog(time.strftime("%H:%M:%S") + "\n")
