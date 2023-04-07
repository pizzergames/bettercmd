import openai
import json
from sys import argv as args
import os

args.pop(0)
args.append('')

wdir = f'{os.getenv("LOCALAPPDATA")}\\bettercmd\\'
if args[0] == '--help':
    print('Ask chatgtp for anything from inside this console')
    print('How it works:')
    print('Run "gptmode --key <your key> to set a key.')
    print('You can create a key by visiting https://platform.openai.com/overview')
    print('Then, make an account. After that, click on the account icon on the upper right corner')
    print('And open click on the "View API keys" button.')
    print('Then, press the "Create new secret key" button. Copy the key and paste it into the command.\n')
elif args[0] == '--key':
    key = args[1]
    with open(f'{wdir}\\openai.json', 'w') as f:
        json.dump({'key': key}, f)
        f.close()
else:
    with open(f'{wdir}\\openai.json', 'r') as f:
        key = json.load(f)['key']
        f.close()
    if key == '':
        print('ERROR: No key availible. Run "chatgpt --key <your key>" to add a key.\nFor further help, type "chatgpt --help"\n')
        exit()
    else:
        openai.api_key = key
        response = openai.Completion.create(
            engine = "text-davinci-003",
            prompt = args[0],
            temperature = 0.6,
            max_tokens = 150,
        )
        print(response.choices[0].text)
