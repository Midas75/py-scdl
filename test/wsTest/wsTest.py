import aiohttp
import asyncio
import queue
import time
import threading

msgQueue = queue.Queue()


async def listen(ws):
    while True:
        msg = await ws.receive()
        if msg.type == aiohttp.WSMsgType.TEXT:
            print(msg.data)
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            print("CLOSED")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ERROR")
            break


async def send(ws):
    while True:
        if msgQueue.empty():
            await asyncio.sleep(3)
        else:
            msg = msgQueue.get(block=False)
            if msg is not None:
                await ws.send_json(msg)


async def writeToQueue():
    while True:
        await asyncio.sleep(3)
        msgQueue.put({"type": "log", "message": time.strftime("%H:%M:%S")})


async def run():
    session = aiohttp.ClientSession()
    async with session.ws_connect(
        "ws://192.168.3.4:3100/sws",
        headers={
            "Service-Name": "all",
            "Hostname": "192.168.30.61",
            "Port": str(3101),
        },
    ) as ws:
        await asyncio.gather(listen(ws), send(ws))


def start():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())


if __name__ == "__main__":
    wsThread = threading.Thread(target=start)
    wsThread.daemon = True
    wsThread.start()
    asyncio.run(writeToQueue())
