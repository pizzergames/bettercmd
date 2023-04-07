from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
        print('Changes the directory')
        print('Syntax: "cd <directory>"')
else:
    name = args[0]
    os.chdir(name)