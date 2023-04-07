from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Display help')
    print('Syntax: "help"')
else:
    with open(f'{os.path.split(__file__)[0]}\\help.txt', 'r') as f:
        text = f.read()
        f.close()
    print(text)
