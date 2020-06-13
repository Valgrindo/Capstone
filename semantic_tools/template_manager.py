"""
Contains functionality related to user-defined Command Templates.

:author: Sergey Goldobin
:date: 06/11/2020 14:56
"""

import argparse
from typing import *

from semantic_tools.logical_form import LogicalForm, CommandTemplateError
from bs4 import BeautifulSoup, Tag


class Command:
    """
    A representation of a recognized Command. Contains the underlying logical form,
    name, and bound parameters.
    """

    def __init__(self, name: str):
        """
        Create a new Command.
        :param name: Command name.
        """
        self.name = name
        # A reference to the template defining this command.
        # A list is nessesary to accomodate multiple top-level components.
        self.template = []  # type: List[LogicalForm]
        self.bound_params = {}  # type: Dict[str: str] # This will be populated with all params bound in the LF tree.

    def __str__(self):
        return f'<command {self.name} -> {self.bound_params}/>'

    def __repr__(self):
        return self.__str__()


class TemplateManager:
    """
    Handle loading, validating, and pattern matching for Command Templates.
    """
    # TODO: As it stands, all templates must be in a single file. However, given the ID->from_ID system, there is
    # TODO: nothing stopping an expansion to a directory with multiple files for ultimate modularity.
    # TODO: Gotta look into that if I get the time.

    def __init__(self, template_file: str):
        """
        Initialize this manager with a file of Templates.
        :param template_file: A file containing a series of command template definitions.
        """
        with open(template_file, 'r') as fp:
            bs = BeautifulSoup(fp, 'xml')

        # Expected structure is a root <commands> tag followed by a series of <command> and <component> definitions.
        root = bs.find('commands')
        if len(root) == 0:
            raise CommandTemplateError('Missing root <commands> tag.')

        self._unresolved_comps = {}  # type: Dict[str: LogicalForm.Component]
        self._parsed_commands = {}  # type: Dict[str: Command]

        for elem in root.children:
            if not isinstance(elem, Tag):
                continue  # Skip junk elements

            cmd = None
            # Two kinds of children are possible: a <command> and a <component>
            if elem.name == 'component':
                # This is a standalone component. It is expected to be used elsewhere, so it must be explicitly named.
                comp = LogicalForm(template=elem, require_id=True)
                self._unresolved_comps[comp.my_id] = comp
            elif elem.name == 'command':
                # A command has a name an candidate root components.
                if 'name' not in elem.attrs:
                    raise CommandTemplateError('Command missing a name attribute.')
                cmd = Command(name=elem.attrs['name'])
                if cmd.name in self._parsed_commands:
                    raise CommandTemplateError(f'Duplicate command name {cmd.name}')

                children = list(filter(lambda c: isinstance(c, Tag), elem.children))
                for c_comp in children:
                    if c_comp.name != 'component':
                        raise CommandTemplateError(f'Unexpected top-level tag under <command>: {c_comp.name}. Only '
                                                   f'<component> allowed.')
                    comp_lf = LogicalForm(template=c_comp)
                    cmd.template.append(comp_lf)
            else:
                # Illegal tag detected.
                raise CommandTemplateError(f'Unexpected tag {elem.name}')

            if cmd:
                self._parsed_commands[cmd.name] = cmd  # Add the command to the library.

        # After the file has been processed, we are left with a set of "loose" components and
        # a set of potentially unresolved commands.
        # Go through the commands and attempt to resolve them.
        for command in self._parsed_commands.values():
            for lf in command.template:
                if not lf.resolved:
                    lf.resolve(self._unresolved_comps)

    def match(self, lf: LogicalForm) -> Optional[Command]:
        """
        Given a Logical Form of a sentence, match it against this manager's template library. If a command is matched
        successfully, return it.
        # TODO: Is there any value in allowing "fuzzy" matching for command that match 90% or something like that?
        :param lf: The logicalForm of a sentence.
        :return: A Command if one was matched.
        """
        raise NotImplementedError("TemplateManager.match()")


# If running in script mode, get the source file as command line arg.
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("templates", help="A file with a series of <command> and <component> definitions.")
    arg_parser.add_argument("sentence", help="A sentence to be matched against the templates.")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Enables additional output.")
    args = arg_parser.parse_args()

    # This is not meant to be a dependency of TemplateManager for the sake of decoupling, but it is useful to be able to
    # exercise the manager if command line mode.
    from semantic_tools.parser import TripsAPI

    tm = TemplateManager(args.templates)
    api = TripsAPI()

    result = api.parse(args.sentence)
    #print(f'Input sentence parse to:\n{result.pretty_format()}')
    print('\nTemplate matching result:\n NOT IMPLEMENTED')
