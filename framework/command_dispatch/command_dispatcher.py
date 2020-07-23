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

from framework.semantic_tools.template_manager import Command

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
                # At least one argument or group is required
                if "args" not in data and "groups" not in data:
                    raise CommandDispatcher.DispatchMapException('Either "args" or "groups" key required for GET mapping.')

                if "args" in data and not data["args"]:
                    raise CommandDispatcher.DispatchMapException('Empty arguments set in a GET mapping.')

                if "groups" in data and not data["groups"]:
                    raise CommandDispatcher.DispatchMapException('Empty groups set in a GET mapping.')

                if "args" in data:
                    self.args = data["args"]
                if "groups" in data:
                    self.groups = data["groups"]

            elif self.type is MappingType.INVOKE:
                for field in INVOKE_FIELDS:
                    if field not in data:
                        raise CommandDispatcher.DispatchMapException(f'Missing required {field} key for INVOKE mapping.')
                    setattr(self, field, data[field])  # Dynamically create the relevant fields

                self.args = [] if "args" not in data else data["args"]
                self.groups = [] if "groups" not in data else data["groups"]
                self.class_ = None if "class" not in data else data["class"]
            else:
                raise CommandDispatcher.DispatchMapException(f'Invalid command type {data["type"]}')

        def __str__(self):
            if self.type is MappingType.GET:
                return f'name: {self.name}\n' + \
                        f'\targs: {self.args}\n' + \
                        f'\tgroups: {self.groups}'
            elif self.type is MappingType.INVOKE:
                return f'name: {self.name}\n' + \
                        f'\targs: {self.args}\n' + \
                        f'\tgroups: {self.groups}\n' + \
                        f'\tmodule: {self.module}\n' + \
                        f'\tclass: {self.class_}\n' + \
                        f'\tmethod: {self.method}'
            else:
                return 'ERROR'

    def __init__(self, dispatch_map: str):
        """
        Initialize a CommandDispatcher using a given Dispatch Map.
        :param dispatch_map: A JSON mapping of commands to modules and functions.
        """
        self._mappings = {}  # type: Dict[str, CommandDispatcher.CommandMapping]

        file_data = None
        try:
            fp = open(dispatch_map, 'r')
            file_data = json.load(fp)
            fp.close()
        except json.decoder.JSONDecodeError as de:
            raise ValueError(f'Malformed dispatch mapping file {dispatch_map}: {de}')

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

            # If the templates are a directory, prepend the context path to all file names
            to_read = [item] if isfile(item) else list(map(lambda x: join(item, x), listdir(item)))

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

    @property
    def modules(self):
        """
        An iterator over module names required for the dispatcher.
        :return:
        """
        for desc in self._mappings.values():
            if hasattr(desc, 'module'):
                yield desc.module
            else:
                continue

    def dispatch(self, command: Command, modules: Dict[str, Any] = None) -> \
            Union[Tuple[Dict[str, str], Dict[str, str]], Optional[Any]]:
        """
        Given a command, execute it using stored descriptions.
        :param command: A Command instance.
        :param modules: A dictionary of loaded modules.
        :return: The output of the invoked function call if there was any OR the GET mapping arguments and groups.
        """
        # Check that the command is actually mapped. This should never happen due to startup validation,
        # but defencive programming is good.
        if command.name not in self._mappings:
            raise ValueError(f'No mappings found for command "{command.name}"')

        desc = self._mappings[command.name]
        if desc.type is MappingType.GET:
            # A GET command needs no invocation, simply return the bound parameters.
            return command.bound_params, command.groups

        if desc.module not in modules:
            raise ValueError(f'Required module {desc.module} not found.')

        module = modules[desc.module]
        # To execute the command we need to perform the following steps:
        # 1) Load the module -- provided by pipeline to avoid duplicating work.
        # 2) Access the module/class method
        # 3) Invoke the method using parameters bound by the command.from
        func_ref = module if desc.class_ is None else getattr(module, desc.class_)
        func = getattr(func_ref, desc.method)

        # The call
        res = func(**command.bound_params)

        return res


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



