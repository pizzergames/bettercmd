import json
import datetime
from sys import argv as args
import os

args.pop(0)
args.append('')

wdir = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'

if args[0] == '--help':
    print('BetterCMD install manager')
    print('Commands:')
    print('    install <path to program> <name>')
    print('        Adds a program to the bettercmd path')
    print('        <path to program> is the path to the .exe')
    print('        <name> is the command to be associated woth the .exe')
    print('        When the file is moved by this program, the path entry will be changed')
    print('    uninstall <name>')
    print('        <name> is the command to uninstall')
    print('    list')
    print('        lists every program installed')
elif args[0] == 'install':
    path = args[1]
    name = args[2]
    entry = {name: [path, str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))]}
    with open(f'{wdir}\\path.json', 'r') as f:
       pathstruct = json.load(f)
    commands = list(pathstruct.keys())
    if name in commands:
        confirm = input(f'WARNING: command {name} already exists. Overwrite entry? [Y/N]: ').upper()
        if confirm == 'Y':
            pathstruct.update(entry)
        else:
            exit()
    else:
        pathstruct.update(entry)
    with open(f'{wdir}\\path.json', 'w') as f:
        json.dump(pathstruct, f)
elif args[0] == 'uninstall':
    name = args[1]
    confirm = input(f'Confirm Uninstall of {name}? [Y/N]: ').upper()
    if confirm == 'Y':
        with open(f'{wdir}\\path.json', 'r') as f:
            pathstruct = json.load(f)
        pathstruct.pop(name)
        with open(f'{wdir}\\path.json', 'w') as f:
            json.dump(pathstruct, f)
    else:
        exit()
elif args[0] == 'list':
    with open(f'{wdir}\\path.json', 'r') as f:
        pathstruct = json.load(f)
    keys = list(pathstruct.keys())
    vals = list(pathstruct.values())
    datas = [keys, vals]
    print('List of every installed Program')
    for key, value in datas:
        name = key
        path, date = value
        thingie = f'{name} links to {path} and was installed on {date}'
        print(thingie)
