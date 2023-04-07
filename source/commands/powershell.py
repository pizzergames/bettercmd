from sys import argv as args
import subprocess

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Run powershell commands from within this console by typing "powershell <command>"\n')
else:
    cmd = ''
    for arg in args:
        cmd += f'{arg} '
    print(subprocess.run(["powershell", cmd], capture_output=True, text=True).stdout, '\n', sep = '')
