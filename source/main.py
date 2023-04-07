import os
import sys
import shutil
import openai
import json
import subprocess
import webbrowser
import time
import datetime
import traceback

#os.chdir(os.path.split(__file__)[0])

sys.argv.append('')

os.system('cls')

wdir = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'

def init():
    directory = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'
    if not os.path.isdir(directory):
        os.mkdir(directory)
        with open(f'{wdir}\\path.json', 'w') as f:
            json.dump({'': ['', '']}, f)
        with open(f'{wdir}\\openai.json', 'w') as f:
            json.dump({'key': ''}, f)
        with open(f'{wdir}\\setting.json', 'w') as f:
            json.dump({}, f)
    print('''
  ____  ______ _______ _______ ______ _____  
 |  _ \\|  ____|__   __|__   __|  ____|  __ \\ 
 | |_) | |__     | |     | |  | |__  | |__) |
 |  _ <|  __|    | |     | |  |  __| |  _  / 
 | |_) | |____   | |     | |  | |____| | \\ \\ 
 |____/|______|  |_|     |_|  |______|_|  \\_\\
             ______________  __________ 
            __  ____/__   |/  /__  __ \\
            _  /    __  /|_/ /__  / / /
            / /___  _  /  / / _  /_/ / 
            \____/  /_/  /_/  /_____/  
        Version 0.1.0''')
    print(
'''#######################################################################################
# Welcome to BetterCmd!                                                               #
# This program is intended to imporove the standart Windows command prompt.           #
#                                                                                     #
# You can`t completely replace the standart console with this, but i`m working on it. #
# DISCLAIMER: This is not a real microsoft product.                                   #
# Have fun!                                                                           #
#######################################################################################
'''
)

#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

def main():
    while True:
        command = input(f'[ BETTERCMD CONSOLE ] @ <{os.getcwd()}> >>> ')
        cmdsplit = command.split(' ')
        line = cmdsplit.pop(0)
        args = cmdsplit
        args.append('')
        pythoninst = f'{line}({args})'
        if line == 'exit':
            break
        argstr = ''
        for arg in args:
            argstr += f'{arg} '
        try:
            #print(f'Generated internal command is: {pythoninst}')
            path = f'{os.path.split(__file__)[0]}\\commands\\{line}.exe'
            if not os.path.isfile(path):
                print('ERROR: could not execute command.\nMake sure it is availible in the Standart Library or installed')
            else:
                os.system(f'{path} {argstr}')
        # except FileNotFoundError:
        #     print('ERROR: could not execute command.\nMake sure it is availible in the Standart Library or installed')
        #     print(sys.exc_info())
        except Exception as e:
            print('Error in command')
            string = ''
            for line in traceback.format_exception(e):
                string += line
            print(string)
    print('Exiting...\n')

init()
main()
#help()
