import socket
import threading


def process_client(connection, address):
        data = connection.recv(1024)
        while data:
            print(f"data: {data}")
            connection.sendall(b"+PONG\r\n")
            data = connection.recv(1024)

def main():
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        connection, address = server_socket.accept() # wait for client
        threading.Thread(target=process_client, args=(connection, address)).start()


if __name__ == "__main__":
    main()
