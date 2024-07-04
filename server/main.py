import argparse
import select
import socket
import queue
"""
GET /user-agent HTTP/1.1
Host: localhost:4221
User-Agent: curl/7.64.1
"""

def handle_request(request_data, directory=None):
    from os import scandir
    request_data = request_data.decode('utf8')
    data = request_data.split('\r\n')
    method, path, version = data[0].split()
    headers = {}
    for header in data[1:]:
        if header:
            if ':' in header:
                name, value = header.split(':', 1)
                headers[name.casefold()] = value.strip()
            
    response = "HTTP/1.1 200 OK\r\n"

    if directory:
        file = path.rsplit('/', 1)[-1]
        content = None
        if method == 'POST':
            response = "HTTP/1.1 201 OK\r\n"
            content = data[-1]
            response += "Content-Length: {}\r\n".format(len(content))
            response += "\r\n\r\n"
            f = open(directory + file, 'w')
            f.write(content)
            f.close()
            return response.encode('utf8')
        else:
            for entry in scandir(directory):
                if entry.is_file():
                    if file == entry.name:
                        with open(directory + entry.name, 'r') as f:
                            content = f.read()
                            response += "Content-Type: application/octet-stream\r\n"
                            response += "Content-Length: {}\r\n".format(len(content))
                            response += "\r\n"
                            response += "{}\r\n".format(content)
                            response += "\r\n\r\n"
                            return response.encode('utf8')
            return b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
    elif path == "/user-agent":
        response += "Content-Type: text/plain\r\n"
        response += "Content-Length: {}\r\n".format(len(headers['user-agent']))
        response += "\r\n"
        response += "{}\r\n".format(headers['user-agent'])
    else:
        response += "Content-Type: text/plain\r\n"
        response += "Content-Length: {}\r\n".format(len(path.rsplit('/', 1)[-1]))
        response += "\r\n" 
        response += "{}\r\n".format(path.rsplit('/', 1)[-1])
    response += "\r\n\r\n"
    if request_data.split(" ")[1].startswith("/echo") or request_data.split(" ")[1] == "/" or request_data.split(" ")[1] == "/user-agent":
        return response.encode('utf8')
    else:
        return b"HTTP/1.1 404 Not Found\r\n\r\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', nargs='?', type=str)
    args = parser.parse_args()

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    server_socket.setblocking(0)

    # sockets to read
    inputs = [server_socket]

    # sockets to write
    outputs = []

    message_queues = {}

    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server_socket:
                client_socket, client_addr = server_socket.accept()
                print(f'new connection with {client_addr}')
                client_socket.setblocking(0)
                inputs.append(client_socket)

                message_queues[client_socket] = queue.Queue()
            else:
                data = s.recv(1024)
                if data:
                    message_queues[s].put(data)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()

                    del message_queues[s]
        
        for s in writable:
            try:
                message = message_queues[s].get_nowait()
            except queue.Empty:
                print(f'output queue for {s.getpeername()} is empty')
                outputs.remove(s)
            else: 
                print(f'sending message for {s.getpeername()}')
                response = handle_request(message, directory=args.directory if args.directory else None)
                s.send(response)
        
        for s in exceptional:
            inputs.remove(s)
            print(f'exceptional condition: {s.getpeername()}')
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

if __name__ == "__main__":
    main()
