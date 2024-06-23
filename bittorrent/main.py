import hashlib
import json
import sys

def decode_bencode(bencoded_value):
    def decode(data):
        if data[0:1].isdigit():
            length, rest_data = data.split(b":", 1)
            length = int(length)
            return rest_data[:length], rest_data[length:]
        elif data.startswith(b'i'):
            delimiter = data.find(b'e')
            if delimiter == -1: raise ValueError("Invalid encoded int value")
            return int(data[1:delimiter]), data[delimiter+1:]
        elif data.startswith(b'l'):
            res = []
            data = data[1:]
            while not data.startswith(b'e'):
                value, data = decode(data)
                res.append(value)
            return res, data[1:]
        elif data.startswith(b'd'):
            res = {}
            data = data[1:]
            while not data.startswith(b'e'):
                key, data = decode(data)
                value, data = decode(data)
                res[key.decode()] = value
            return res, data[1:]
        else:
            raise ValueError("Invalid encoded value")
    
    decoded_value, _ = decode(bencoded_value)
    return decoded_value

def encode_bencode(data):
    if isinstance(data, int):
        return f'i{data}e'.encode()
    elif isinstance(data, str):
        return f'{len(data)}:{data}'.encode()
    elif isinstance(data, bytes):
        return f'{len(data)}:'.encode() + data
    elif isinstance(data, list):
        output = b'l'
        for element in data:
            output += encode_bencode(element)
        return output + b'e'
    elif isinstance(data, dict):
        output = b'd'
        for key, value in data.items():
            output += encode_bencode(key) + encode_bencode(value)
        return output + b'e'
    else:
        raise ValueError(f"{type(data)}: not supported")

def listpiecehashes(pieces):
    output = ''
    res = []
    for i, piece in enumerate(pieces):
        if i and i % 20 == 0:
            res.append(output + "\n")
            output = ''
        char = hex(piece)[2:] # remove '0x'
        if len(char) == 1: char = '0' + char # pad 1 character with a '0' 
        output += char
    res.append(output)
    return "".join(res)

def main():
    command = sys.argv[1]
    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode()
            raise TypeError(f"Type not serializable: {type(data)}")
        print(json.dumps(decode_bencode(bencoded_value), default=bytes_to_str))
    elif command == "info":
        with open(sys.argv[2], 'rb') as f:
            bencoded_file = f.read()
        decoded_file = decode_bencode(bencoded_file)
        file_info = decoded_file['info']
        infohash = hashlib.sha1(encode_bencode(file_info)).hexdigest()
        print(f"Tracker URL: {decoded_file['announce'].decode()}\nLength: {file_info['length']}")
        print(f"Info Hash: {infohash}\nPiece Length: {file_info['piece length']}")
        print(f"Piece Hashes:\n{listpiecehashes(file_info['pieces'])}")
    else:
        raise NotImplementedError(f"Unknown command {command}")

if __name__ == "__main__":
    main()
