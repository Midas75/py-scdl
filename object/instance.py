from pydantic import BaseModel
class Instance(BaseModel):
    serviceName: str
    hostname: str
    port: int
    def __str__(self):
        return "{}-{}-{}".format(self.serviceName, self.hostname, self.port)


