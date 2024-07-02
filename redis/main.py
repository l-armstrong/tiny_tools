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

store = {}

# def parse_resp(data):
#     """ Redis serialization protocol parser
#         https://redis.io/docs/latest/develop/reference/protocol-spec/
#     """
#     import datetime
#     client_request = [
#         element 
#         for element in data.decode().split()
#         if not (element.startswith("$") or element.startswith("*"))
#     ]
#     command = client_request[0]
#     match command.lower():
#         case "ping":
#             return "+PONG\r\n".encode()
#         case "echo":
#             arg = client_request[1]
#             return f'${len(arg)}\r\n{arg}\r\n'.encode()
#         case "set":
#             key, value = client_request[1], client_request[2]
#             if 'px' in client_request:
#                 expiry = client_request[client_request.index('px') + 1]
#                 store[key] = (value, datetime.datetime.today() + datetime.timedelta(milliseconds=int(expiry)))
#             else:
#                 store[key] = (value, None)
#             return "+OK\r\n".encode()
#         case "get":
#             if (key := client_request[1]) in store and (not store[key][1] or store[key][1] >= datetime.datetime.today()):
#                 value = store[key][0]
#                 return f'${len(value)}\r\n{value}\r\n'.encode()
#             return "$-1\r\n".encode() # Key doesn't exist. Return null bulk string

def parse_resp(data):
    """ Redis serialization protocol parser
        https://redis.io/docs/latest/develop/reference/protocol-spec/
    """
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
        case "set":
            key, value = client_request[1], client_request[2]
            if 'px' in client_request:
                expiry = float(client_request[client_request.index('px') + 1])
                # Delete the key in a seperate thread when the key expires
                threading.Timer(expiry / 1000, lambda key: store.pop(key), (key,)).start()
            store[key] = value
            return "+OK\r\n".encode()
        case "get":
            if (key := client_request[1]) in store:
                value = store[key]
                return f'${len(value)}\r\n{value}\r\n'.encode()
            return "$-1\r\n".encode() # Key doesn't exist. Return null bulk string

def process_client(connection, address):
    while data := connection.recv(1024):
        response = parse_resp(data)
        connection.sendall(response)

def main():
    import sys
    port = 6379
    if len(sys.argv) > 1 and ('--port' in sys.argv):
        port = int(sys.argv[sys.argv.index('--port') + 1])

    server_socket = socket.create_server(("localhost", port), reuse_port=True)
    while True:
        connection, address = server_socket.accept() # wait for client
        threading.Thread(target=process_client, args=(connection, address)).start()


if __name__ == "__main__":
    main()
