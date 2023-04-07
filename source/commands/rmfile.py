from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Deletes a file')
    print('Syntax: "rmfile <file>"')
else:
    name = args[0]
    os.remove(name)
