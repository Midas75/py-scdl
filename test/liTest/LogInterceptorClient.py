import sys
import socket

class OutputInterceptor:
    def __init__(self, remote_host, remote_port):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.original_stdout = sys.stdout
        self.socket = None

    def start(self):
        # 重定向标准输出到自定义的文件描述符
        sys.stdout = self

        # 连接到远程服务器
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.remote_host, self.remote_port))

    def stop(self):
        # 恢复原本的标准输出
        sys.stdout = self.original_stdout

        # 关闭网络连接
        if self.socket:
            self.socket.close()

    def write(self, text):
        # 发送输出到远程服务器
        self.original_stdout.write(text)
        if self.socket:
            self.socket.send(text.encode())

    def flush(self):
        pass

if __name__ == "__main__":
    remote_host = "127.0.0.1"
    remote_port = 12345

    interceptor = OutputInterceptor(remote_host, remote_port)
    interceptor.start()

    try:
        # 你的程序逻辑
        print("这个输出会被拦截并发送到远程服务器")
        print("原本的标准输出逻辑不受影响")

    finally:
        interceptor.stop()
