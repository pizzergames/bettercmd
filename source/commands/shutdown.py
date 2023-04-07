from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Shuts down the computer')
    print('Syntax: "shutdown"')
else:
    os.system('shutdown')
