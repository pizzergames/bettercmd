from sys import argv as args
import shutil
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Removes a Folder')
    print('Syntax: "rmdir <folder>"')
else:
    name = args[0]
    try:
        os.rmdir(name)
    except OSError:
        confirm = input('WARNING: Directory is not empty. Continue anyways? [Y/N]: ').upper()
        if confirm == 'Y':
            shutil.rmtree(name)
        else:
            exit()
