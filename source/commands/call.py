from sys import argv as args
import os

args.pop(0)
args.append('')

wdir = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'

if args[0] == '--help':
    print('Executes another .bat/.cmd file')
    print('Syntax: "call <file>"')
else:
    cmd = ''
    for arg in args:
        cmd += f'{arg} '
    os.system(cmd)