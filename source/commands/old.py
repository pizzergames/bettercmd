from sys import argv as args
from os import system

if args[0] == '--help':
    print('Uses the old console to execute a command for compatability')
    print('Syntax: "old <command>"')
else:
    command = ''
    for arg in args:
        command += f'{arg} '
    system(command)
