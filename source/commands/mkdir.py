from sys import argv as args
import os

if args[0] == '--help':
    print('Creates a new Folder')
    print('Syntax: "mkdir <name>"')
else:
    name = args[0]
    os.mkdir(name)
