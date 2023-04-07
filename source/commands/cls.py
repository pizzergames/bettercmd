from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Clears the Screen')
    print('Syntax : "cls"')
else:
    os.system('cls')