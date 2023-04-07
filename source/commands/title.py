from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Sets the title of the Window')
    print('Syntax: "title <name>"')
else:
    name = args[0]
    os.system(f'title {name}')
