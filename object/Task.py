class TaskType:
    LOG = 0
    CLOSE = 1
    ROUTE = 2
    CONFIG = 3


class Task:
    def __init__(self, type: TaskType, data=None):
        self.type = type
        self.data = data
