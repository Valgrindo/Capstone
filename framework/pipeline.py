"""
A file that joins all the Voice Control framework components into a pipeline.
This is the only file that needs to be accessed by (and imported into) the host application.

:author: Sergey Goldobin
:date: 06/26/2020 13:34

CS 788.01 Master's Capstone Project
"""

from os.path import isfile
from typing import *
import json
import argparse

CONFIGURATION = "configuration.json"  # Expected name and location of the config file.
TUTORIAL = "tutorial.txt"
USAGE = """pipeline.py [-h] [-v]

optional arguments:
 -h, --help         Show a brief tutorial on framework usage.
 -v, --validate     Validate the current state of framework configuration.
"""


class Pipeline:
    """
    A singleton pipeline containing all the configuration set up by the host application.
    """
    pass


def validate_framework_state(config: Dict[str, str]) -> bool:
    """
    Verify that the framework is functional in its current state.
    :param config: A JSON configuration object.
    :return:
    """
    pass


"""
An option to run this in script mode to validate the current configuration.
The framework folder contains a configuration file that specifies where to pull command templates and command dispatch
mappings from.
"""
if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(usage=USAGE)
    arg_parser.add_argument("-v", "--validate", action="store_true",
                            help="Validate all framework components.")
    args = arg_parser.parse_args()

    # If neither flag was specified, there is nothing to do.
    if not (args.validate and args.help):
        arg_parser.print_usage()
        print('\nVoice Control Integration Pipeline\n',
              'Copyright © 2020 by Sergey Goldobin')
        exit(0)

    # TODO: Is there a way to prevent the file from tampering without baking it into the code?
    if args.help:
        with open(TUTORIAL, 'r') as fp:
            print(fp.read())
        exit(0)

    # Validation was selected, proceed.

    # First, check that the config file exists.
    if not isfile(CONFIGURATION):
        print(f'Configuration file ./{CONFIGURATION} not found.')
        exit(1)

    try:
        with open(CONFIGURATION, 'r') as fp:
            conf_obj = json.load(fp)

        framework_state = validate_framework_state(conf_obj)
    except json.decoder.JSONDecodeError as de:
        print(f'Failed to parse configuration file: {de}')
        exit(1)
    except ValueError as ve:
        print(f'Framework state error: {ve}')
        exit(1)

    # If made it to the end with no errors, all the framework components are ready to go.
    print('Framework is functional!')

