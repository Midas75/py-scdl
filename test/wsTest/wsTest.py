import websocket
import rel
ws = websocket.WebSocketApp(
    "ws://192.168.30.61:3100/sws"
)
ws.run_forever(dispatcher=rel, reconnect=5)
rel.signal(2, rel.abort)
rel.dispatch()
print("after")


