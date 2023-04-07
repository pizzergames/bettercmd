from sys import argv as args

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Displays the version of the program')
    print('Syntax: "version"')
else:
    print('Program Version: Full Release 1.0')
    print('Python Version: 3.11.1')
