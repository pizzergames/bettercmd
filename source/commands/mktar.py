from sys import argv as args
import shutil
import os

if args[0] == '--help':
    print('Makes a tar archive out of a folder')
    print('Syntax: "mktar <folder>"')
else:
    name = args[0]
    print('Creating .tar archive...')
    shutil.make_archive(os.path.split(name)[0], 'tar', name)
