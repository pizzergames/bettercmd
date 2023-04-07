from sys import argv as args

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Outputs whatever is in a file to the console')
    print('Syntax: "type <file>"')
else:
    file = args[0]
    with open(file, 'r') as f:
        print(f.read())
        f.close()
