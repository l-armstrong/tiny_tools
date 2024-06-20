import os
import sys

def echo(*args):
    for i, x in enumerate(args):
        if i != len(args) - 1: sys.stdout.write(x + ' ')
        else: sys.stdout.write(x + '\n')
    sys.stdout.flush()

def search_command(command, args):
    import subprocess 
    for f in os.environ['PATH'].split(":"):
        command_path = f'{f}/{command}'
        if os.path.isdir(f) and os.path.isfile(command_path):
            subprocess.run([command_path, *args])
            break
    else:
        print(f'{command}: not found')

def commandtype(*args):
    for command in args:
        if command in builtin_commands:
            print(f'{command} is a shell builtin')
        else:
            for f in os.environ["PATH"].split(":"):
                if os.path.isdir(f) and command in os.listdir(f):
                    print(f"{f}/{command}")
                    break
            else:
                print(f"{command}: not found")
        
builtin_commands = {
    "exit": lambda x: exit(int(x)), 
    "echo": echo, 
    "type": commandtype
}

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        command, *args = input().split()
        if command not in builtin_commands:
            search_command(command, args)
        else:
            builtin_commands[command](*args)

if __name__ == "__main__":
    main()
