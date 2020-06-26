"""
This module is responsible for the actions of the pipeline beyond command template matching. This module parses and
validates dispatch maps loaded into the framework, and passes on command arguments from a template to a return/func call.

:author: Sergey Goldobin
:date: 06/22/2020 14:35
"""

import argparse
import json
from os.path import isfile, isdir, split, join
from os import listdir
from bs4 import BeautifulSoup
from typing import *
from enum import Enum

TEMPLATE_KEY = "templates"  # JSON dictionary key for template source listing
COMMAND_KEY = "commands"    # JSON dictionary key for mapping description listing
CMD_NAME_KEY = "name"       # JSON dictionary key for command name

META_KEYS = ["templates", "commands"]
GENERAL_FIELDS = ["name", "type"]
INVOKE_FIELDS = ["method", "module"]
GET_FIELD = "args"
XML_EXT = ".xml"


class MappingType(Enum):
    """
    An enumeration of different types of mappings.
    """
    GET = "GET",
    INVOKE = "INVOKE",
    ERROR = ""

    @staticmethod
    def parse(item: str):
        if not isinstance(item, str):
            return MappingType.ERROR

        try:
            return MappingType[item]
        except KeyError:
            return MappingType.ERROR


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

        def __init__(self, data: Dict[str, str]):
            self.name = data["name"]
            self.type = MappingType.parse(data["type"])

            if self.type is MappingType.GET:
                # At least one argument is required
                if "args" not in data:
                    raise CommandDispatcher.DispatchMapException('Missing required "args" key for GET mapping.')

                if not data["args"]:
                    raise CommandDispatcher.DispatchMapException('Empty arguments set in a GET mapping.')

                self.args = data["args"]
            elif self.type is MappingType.INVOKE:
                for field in INVOKE_FIELDS:
                    if field not in data:
                        raise CommandDispatcher.DispatchMapException(f'Missing required {field} key for INVOKE mapping.')
                    setattr(self, field, data[field])  # Dynamically create the relevant fields

                if "args" in data:
                    self.args = data["args"]  # Args are optional for invokes
                if "class" in data:
                    self.class_ = data["class"]  # Class is optional for invokes

            else:
                raise CommandDispatcher.DispatchMapException(f'Invalid command type {data["type"]}')

        def __str__(self):
            if self.type is MappingType.GET:
                return f'name: {self.name}\n' + \
                        f'\targs: {self.args}'
            elif self.type is MappingType.INVOKE:
                return f'name: {self.name}\n' + \
                        f'\targs: {self.args}\n' + \
                        f'\tmodule: {self.module}\n' + \
                        f'\tclass: {self.class_}' + \
                        f'\tmethod: {self.method}'
            else:
                return 'ERROR'

    def __init__(self, dispatch_map: str):
        """
        Initialize a CommandDispatcher using a given Dispatch Map.
        :param dispatch_map: A JSON mapping of commands to modules and functions.
        """
        self._mappings = {}  # type: Dict[str, CommandDispatcher.CommandMapping]

        fp = open(dispatch_map, 'r')
        file_data = json.load(fp)
        fp.close()

        context_path = split(dispatch_map)[0]  # The context for files referenced in the map

        # First, check that a valid set of template files were supplied. Gather the set of commands named in the files.
        # Actual command validation is up to the TemplateManager. DOes not occur here, but will in the unified pipeline,
        # since the template parsing step would precede this.
        if TEMPLATE_KEY not in file_data:
            raise CommandDispatcher.DispatchMapException("Template source attribute 'templates' not found.")

        cmd_names = set()  # type: Set[str]

        for item in file_data[TEMPLATE_KEY]:
            item = join(context_path, item)
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
                    cmd_names.add(t.attrs['name'])

        # Now that all available names have been retrieved, check the list of command mappings for violations.
        if COMMAND_KEY not in file_data:
            raise CommandDispatcher.DispatchMapException("Command mapping attribute 'commands' not found.")

        # Every mapping must have a name and a type
        # For GET mappings, at least one ARG is required
        # for INVOKE mappings, module and method are required
        for desc in file_data[COMMAND_KEY]:
            if desc[CMD_NAME_KEY] not in cmd_names:
                raise CommandDispatcher.DispatchMapException(f"Undefined command {desc[CMD_NAME_KEY]}")

            mapping = CommandDispatcher.CommandMapping(desc)

            # Everything is correct. Copy the mapping.
            self._mappings[mapping.name] = mapping

    def dump(self) -> str:
        """
        Convert this dispatcher into a string.
        :return:
        """
        return '\n'.join(map(str, self._mappings.values()))

    def __iter__(self):
        """
        An iterator over internal mappings.
        :return:
        """
        for mapping in self._mappings.values():
            yield mapping


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
    print(cd.dump())



