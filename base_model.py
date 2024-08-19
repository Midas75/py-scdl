from pydantic import BaseModel


class Instance(BaseModel):
    serviceName: str
    hostname: str
    port: int

    def __str__(self):
        return f"{self.serviceName}-{self.hostname}-{self.port}"


class ServerConfig(BaseModel):
    host: str
    port: int = 3100

    def __str__(self) -> str:
        return f"http://{self.host}:{self.port}"