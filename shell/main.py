import sys

def echo(*args):
    for i, x in enumerate(args):
        if i != len(args) - 1: sys.stdout.write(x + ' ')
        else: sys.stdout.write(x + '\n')
    sys.stdout.flush()

def commandtype(*args):
    for command in args:
        if command in commands:
            print(f'{command} is a shell builtin')
        else:
            print(f'{command}: not found')

commands = {
    "exit": lambda x: exit(int(x)), 
    "echo": echo, 
    "type": commandtype
}

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        command, *args = input().split()

        if command not in commands:
            print(f'{command}: command not found')
        else:
            commands[command](*args)

if __name__ == "__main__":
    main()
