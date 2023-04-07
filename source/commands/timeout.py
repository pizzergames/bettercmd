from sys import argv as args
import time

args.pop(0)
args.append('')

if args[0] == '--help':
    print('Sleeps for x seconds')
    print('Syntax: "timeout <seconds>"')
else:
    wait = float(args[0])
    time.sleep(wait)
