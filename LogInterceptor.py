import sys
from typing import TextIO
from ILog import ILog


class LogInterceptor:
    def __init__(self, target: ILog, original_stdout: TextIO = sys.stdout):
        self.original_stdout = original_stdout
        self.target = target
        sys.stdout = self

    def __del__(self):
        return self.stop()

    def stop(self) -> None:
        sys.stdout = self.original_stdout

    def write(self, message):
        self.target.doLog(message)
        return self.original_stdout.write(message)

    def flush(self) -> None:
        return self.original_stdout.flush()
