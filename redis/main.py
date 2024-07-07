import socket
import threading

store = {}
repl_sockets = []

def parse_resp(data, connection, server_info):
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
            for repl in repl_sockets:
                repl.send(data)
            return "+OK\r\n".encode()
        case "get":
            if (key := client_request[1]) in store:
                value = store[key]
                return f'${len(value)}\r\n{value}\r\n'.encode()
            return "$-1\r\n".encode() # Key doesn't exist. Return null bulk string
        case "info":
            if client_request[1] == "replication":
                value = f"role:{server_info["role"]}"
                if server_info["role"] == "master":
                    value += f"master_replid:{server_info["master_replid"]}"
                    value += f"master_repl_offset:{server_info["master_repl_offset"]}"
                output = f'${len(value)}\r\n{value}\r\n'
                return output.encode()
        case "replconf":
            return "+OK\r\n".encode()
        case "psync":
            if "?" in client_request and "-1" in client_request:
                output = f"+FULLRESYNC {server_info["master_replid"]} 0\r\n"
                empty_rdb_content = bytes.fromhex("524544495330303131fa0972656469732d76657205372e322e30fa0a72656469732d62697473c040fa056374696d65c26d08bc65fa08757365642d6d656dc2b0c41000fa08616f662d62617365c000fff06e3bfec0ff5aa2")
                output += f"${len(empty_rdb_content)}\r\n"
                repl_sockets.append(connection)
                return output.encode() + empty_rdb_content


def process_client(connection, server_info):
    while data := connection.recv(1024):
        response = parse_resp(data, connection, server_info)
        connection.sendall(response)

def main():
    import argparse 
    import random
    import string 
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=6379)
    parser.add_argument("--replicaof")
    args = parser.parse_args()
    server_socket = socket.create_server(("localhost", args.port), reuse_port=True)
    role = "master" if not args.replicaof else "slave"
    master = (role == "master")
    master_replid = "".join(random.choices(string.ascii_letters + string.digits, k=40))
    master_host, master_port = args.replicaof.split() if args.replicaof else (None, None)
    server_info = {
        "socket": server_socket,
        "port": args.port,
        "role": role,
        "master_replid": master_replid if master else None,
        "master_repl_offset": 0 if master else None,
        "master_host": master_host,
        "master_port": master_port,
    }
    if args.replicaof:
        # initiate handshake
        # send PING to master server 
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        master_socket.connect((master_host, int(master_port)))
        master_socket.sendall(b"*1\r\n$4\r\nPING\r\n")
        # recv "PONG" from master
        master_socket.recv(4)
        # send REPLCONF twice to master server 
        master_socket.sendall(f"*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n{args.port}\r\n".encode()) 
        # recv "OK" from master
        master_socket.recv(4)
        # send PSYNC capabilities to to master
        master_socket.sendall(b"*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n")
        # recv "OK" from master
        master_socket.recv(4)
        # send PSYNC command to sync. state of replica to master
        master_socket.sendall(b"*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n")
        # recv simple string
        master_socket.recv(1024)

    while True:
        connection, address = server_socket.accept() # wait for client
        threading.Thread(target=process_client, args=(connection, server_info)).start()

if __name__ == "__main__":
    main()
