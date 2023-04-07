from sys import argv as args
import os
import json
import time
import shutil

wdir = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'

args.pop(0)
args.append('')

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
    print(
'''
#######################################################################################
# Welcome to BetterCmd!                                                               #
# This program is intended to imporove the standart Windows command prompt.           #
#                                                                                     #
# You can`t completely replace the standart console with this, but i`m working on it. #
# DISCLAIMER: This is not a real microsoft product.                                   #
# Have fun!                                                                           #
#######################################################################################
'''
)

if args[0] == '--help':
    print('Resets the data of the program. Might help when Errors are accouring')
    print('WARNING: This resets the chatgpt key, the settings and the installed programs')
    print('Syntax: "rstappdata"')
else:
    confirm = input('WARNING: This resets the chatgpt key, the settings and the installed programs\nConfirm? [Y/N]: ').upper()
    if confirm == 'Y':
        shutil.rmtree(wdir)
        print('Restarting...')
        time.sleep(1)
        os.system('cls')
        init()
