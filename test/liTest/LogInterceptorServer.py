import socket

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"等待客户端连接在 {host}:{port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"连接来自 {client_address}")
        handle_client(client_socket)

def handle_client(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(data.decode(), end='')  # 打印接收到的数据

if __name__ == "__main__":
    server_host = "0.0.0.0"
    server_port = 12345

    start_server(server_host, server_port)
