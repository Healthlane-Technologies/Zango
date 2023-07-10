
import argparse
import os
import django

def install_packages(args):
    # Logic to install packages based on the provided arguments
    app_name = args.app_name
    settings_file = args.settings
    print(app_name)
    print(settings_file)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    django.setup()
    from django.conf import settings
    print(settings.BASE_DIR)

    return

def main():
    parser = argparse.ArgumentParser(prog='zelthy3', description='Zelthy3 CLI')

    subparsers = parser.add_subparsers(dest='command')

    # Create a parser for the "install_packages" command
    install_parser = subparsers.add_parser('install_packages', help='Install packages')
    install_parser.add_argument('app_name', type=str, help='Name of the app')
    install_parser.add_argument('--settings', type=str, help='Django settings file')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the appropriate function based on the command
    if args.command == 'install_packages':
        install_packages(args)

if __name__ == '__main__':
    main()