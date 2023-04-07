from sys import argv as args
from os import system

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Sets the color theme')
    print('The color theme will get stored, so it automatically gets applid on startup')
    print('Syntax: "theme <background> <foreground>"')
    print('Forground colors are:')
    print('    grey')
    print('    light-blue')
    print('    light-green')
    print('    light-turquoise')
    print('    light-red')
    print('    light-purple')
    print('    light-yellow')
    print('    white')
    print('\nBackground colors are:')
    print('    Black')
    print('    Blue')
    print('    Green')
    print('    Turquoise')
    print('    Red')
    print('    Purple')
    print('    Yellow')
    print('    Light grey')
    print('\nPreset Themes are:')
    print('    --dark-mode (Default)')
    print('    --light-mode')
    print('    --hacker')
elif args[0] == '--dark-mode':
    system('color 0F')
elif args[0] == '--light-mode':
    system('color 78')
elif args[0] == '--hacker':
    system('color 0A')
else:
    bg, fg = args[0], args[1]
    bgs = {'Black': '0', 'Blue': '1', 'Green': '2', 'Turquoise': '3', 'Red': '4', 'Purple': '5', 'Yellow': '6', 'Light grey': '7'}
    fgs = {'grey': '8', 'light-blue': '9', 'light-green': 'A', 'light-turquoise': 'B', 'light-red': 'C', 'light-purple': 'D', 'light-yellow': 'E', 'white': 'F'}
    cmd = f'color {bgs[bg]}{fgs[fg]}'
    system(cmd)