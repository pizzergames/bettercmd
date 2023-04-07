from sys import argv as args
import os

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Creates a new File')
    print('Syntax: "mkfile <name>"')
else:
    name = args[0]
    if not os.path.isfile(name):
        with open(name, 'x') as f:
            f.write('')
            f.close()
    else:
        print(f'ERROR: file "{name}" already exists.')
        replace = input('Overwrite file? [Y/N]: ').upper()
        if replace == 'Y':
            os.remove(name)
            with open(name, 'x') as f:
                f.write('')
                f.close()
