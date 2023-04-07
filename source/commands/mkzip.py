from sys import argv as args
import shutil
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Makes a zip archive out of a folder')
    print('Syntax: "mktar <folder>"')
else:
    name = args[0]
    print('Creating .tar archive...')
    shutil.make_archive(os.path.split(name)[0], 'zip', name)
