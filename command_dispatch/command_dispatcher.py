"""
This module is responsible for the actions of the pipeline beyond command template matching. This module parses and
validates dispatch maps loaded into the framework, and passes on command arguments from a template to a return/func call.

:author: Sergey Goldobin
:date: 06/22/2020 14:35
"""

import argparse
import json
from os.path import isfile, isdir, splitext
from os import listdir
from bs4 import BeautifulSoup
from typing import *

TEMPLATE_KEY = "templates"  # JSON dictionary key for template source listing
COMMAND_KEY = "commands"    # JSON dictionary key for mapping description listing
CMD_NAME_KEY = "name"       # JSON dictionary key for command name

XML_EXT = ".xml"


class CommandDispatcher:

    class DispatchMapException(Exception):
        """
        A class representing errors with a Dispatch Map.
        """
        # TODO
        pass

    class CommandMapping:
        """
        A collection of surface level information about a command
        """
        pass

    def __init__(self, dispatch_map: str):
        """
        Initialize a CommandDispatcher using a given Dispatch Map.
        :param dispatch_map: A JSON mapping of commands to modules and functions.
        """
        self._mappings = {}  # type: Dict[str, CommandDispatcher.CommandMapping]

        fp = open(dispatch_map, 'r')
        file_data = json.load(fp)
        fp.close()

        # First, check that a valid set of template files were supplied. Gather the set of commands named in the files.
        # Actual command validation is up to the TemplateManager. DOes not occur here, but will in the unified pipeline,
        # since the template parsing step would precede this.
        if TEMPLATE_KEY not in file_data:
            raise CommandDispatcher.DispatchMapException("Template source attribute 'templates' not found.")

        cmd_names = set()  # type: Set[str]

        for item in file_data[TEMPLATE_KEY]:
            # Each item is either an XML file or a directory of XML files.
            if isfile(item) and not item.endswith(XML_EXT):
                raise CommandDispatcher.DispatchMapException(f"Unexpected template file extension for {item}")

            if isdir(item) and any(not f.endswith(XML_EXT) for f in listdir(item)):
                raise CommandDispatcher.DispatchMapException(f"Found non-{XML_EXT} files in template directory {item}")

            to_read = [item] if isfile(item) else listdir(item)

            # For every source file, read all available command names.
            for file in to_read:
                with open(file, 'r') as fp:
                    bs = BeautifulSoup(fp, 'xml')

                tags = bs.findAll('command')
                for t in tags:
                    cmd_names.add(t.name)  # TODO: Add content, not tag name

        # Now that all available names have been retrieved, check the list of command mappings for violations.
        if COMMAND_KEY not in file_data:
            raise CommandDispatcher.DispatchMapException("Command mapping attribute 'commands' not found.")

        for desc in file_data[COMMAND_KEY]:
            if CMD_NAME_KEY not in desc:
                raise CommandDispatcher.DispatchMapException("Command description missing 'name' attribute")

            if desc[CMD_NAME_KEY] not in cmd_names:
                raise CommandDispatcher.DispatchMapException(f"Undefined command {desc[CMD_NAME_KEY]}")

            # TODO: Check for presence of other required attributes: type, args, module, method

            # Everything is correct. Copy the mapping.
            self._mappings[desc[CMD_NAME_KEY]] = desc


if __name__ == '__main__':
    """
    When run as a script, this program takes in a dispatch map and validates it.
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("dispatch_map", help="A JSON file mapping Commands to modules and functions.")
    args = arg_parser.parse_args()

    if not isfile(args.dispatch_map):
        print(f'Error: Dispatch map {args.dispatch_map} not found.')
        exit(1)

    try:
        cd = CommandDispatcher(args.dispatch_map)
    except CommandDispatcher.DispatchMapException as cde:
        print(f'Failed to validate the dispatch map:\n{cde}')
        exit(1)

    # If no exception occurred upon initialization, then the map is good to go.
    print('Dispatch map validated!')



