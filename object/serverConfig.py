from pydantic import BaseModel


class ServerConfig(BaseModel):
    host: str
    port: int=3100

    def __str__(self) -> str:
        return "http://{}:{}".format(self.host, self.port)
