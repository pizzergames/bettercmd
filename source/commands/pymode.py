import traceback
from os import getcwd
from sys import argv as args, version

args.pop(0)
args.append('')

variables = {}
if args[0] == '--help':
    print('Welcome to the pymode help section!\n')
    print('Single arguments:')
    print('    --help              show this help')
    print('    --code <code>       execute a line of code')
    print('    --file <file>       execute a Python (.py) file')
    print('    --version           show the Python version')
elif args[0] == '--code':
    args.pop(0)
    line = ''
    for arg in args:
        line += f'{arg} '
    try:
        exec(line)
    except Exception as e:
        output = traceback.format_exception(e)
        errorstr = ''
        for line in output:
            errorstr += line
        print(errorstr)
elif args[0] == '--version':
    print('Current Python version')
    print(version)
elif args[0] == '--file':
    file = args[1]
    with open(file, 'r') as f:
        script = f.read()
        f.close()
    try:
        exec(script)
    except Exception as e:
        output = traceback.format_exception(e)
        errorstr = ''
        for line in output:
            errorstr += line
        print(errorstr)
else:
    print('BetterCMD PYMODE')
    print(f'Python {version}')
    while True:
        curcommand = str(input(f'[ BETTERCMD PYMODE ] >>> '))
        if 'exit()' in curcommand:
            break
        if ':' in curcommand:
            while True:
                newline = str(input(f'[ BETTERCMD PYMODE ] ... '))
                if newline == '':
                    break
                else:
                    curcommand += f'\n{newline}'
        #print(f'"{curcommand}"')
        try:
            exec(curcommand)
        except Exception as e:
            output = traceback.format_exception(e)
            errorstr = ''
            for line in output:
                errorstr += line
            print(errorstr)
