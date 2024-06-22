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
        print(f"Tracker URL: {decoded_file['announce'].decode()}\nLength: {decoded_file['info']['length']}")
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
