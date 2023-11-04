import requests
import sys
from typing import TextIO
from object.instance import Instance
from object.serverConfig import ServerConfig
import asyncio
from client import Client


class LogInterceptor(Client):
    original_stdout: TextIO
    client: Client

    def __init__(self, client: Client, original_stdout: TextIO = sys.stdout):
        self.original_stdout = original_stdout
        self.client = client
        sys.stdout = self

    def __del__(self):
        return self.stop()

    def stop(self) -> None:
        sys.stdout = self.original_stdout

    def write(self, message):
        asyncio.run(
            self.client.log(message)
        )
        return self.original_stdout.write(message)

    def flush(self) -> None:
        return self.original_stdout.flush()
