from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('The echo command prints something to the console.')
    print('Syntax: "echo <string>"')
else:
    string = ''
    for arg in args:
        string += f'{arg} '
    print(f'{string}\n')
