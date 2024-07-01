import socket
import threading

# *1\r\n$4\r\nPING\r\n -> PING 
# *2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n -> ["ECHO", "hey"]

# WORKS but want to experiement with match command
# def parse_resp(data):
#     command = data.split(b'\r\n')[2]
#     if command.lower() == b"ping":
#         return b"+PONG\r\n"
#     elif command.lower() == b"echo":
#         arg = data.split(b'\r\n')[4]
#         return f'${len(arg)}\r\n{arg.decode()}\r\n'.encode()

def parse_resp(data):
    client_request = [
        element 
        for element in data.decode().split()
        if not (element.startswith("$") or element.startswith("*"))
    ]
    command = client_request[0]
    match command.lower():
        case "ping":
            return "+PONG\r\n".encode()
        case "echo":
            arg = client_request[1]
            return f'${len(arg)}\r\n{arg}\r\n'.encode()

def process_client(connection, address):
    data = connection.recv(1024)
    while data:
        response = parse_resp(data)
        connection.sendall(response)
        data = connection.recv(1024)

def main():
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        connection, address = server_socket.accept() # wait for client
        threading.Thread(target=process_client, args=(connection, address)).start()


if __name__ == "__main__":
    main()
