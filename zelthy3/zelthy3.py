# zelthy3.py

import argparse
from django.core import management

def newproject(args):
    print("here")
    from django.core.management import get_commands
    print(get_commands())
    management.call_command('newproject', args.name)

def main():
    parser = argparse.ArgumentParser(prog='zelthy3')
    subparsers = parser.add_subparsers()
    print("inside main")

    newproject_parser = subparsers.add_parser('newproject')
    newproject_parser.add_argument('name')
    newproject_parser.set_defaults(func=newproject)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
