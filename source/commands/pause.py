from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('pauses the console until a key is pressed')
    print('Syntax: "pause"')
else:
    os.system('pause')