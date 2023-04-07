from sys import argv as args
import shutil

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Move a file/folder')
    print('Syntax: "move <source> <destination>"')
else:
    src = args[0]
    dst = args[1]
    shutil.move(src, dst)