from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    pass
else:
    files = os.listdir()
    filetype = args[0]
    for file in files:
        if not filetype == '':
            if os.path.isfile():
                if f'.{filetype.upper()}' == os.path.splitext(file)[1].upper():
                    print(f'{filetype.upper()}...')
