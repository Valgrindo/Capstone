"""
Contains functionality related to user-defined Command Templates.

:author: Sergey Goldobin
:date: 06/11/2020 14:56
"""

import argparse
from typing import *
from os.path import isfile, join, isdir
from os import listdir

from logical_form import LogicalForm, CommandTemplateError
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
        # A list is necessary to accommodate multiple top-level components.
        self.template = []  # type: List[LogicalForm]
        self.bound_params = {}  # type: Dict[str: str] # This will be populated with all params bound in the LF tree.

    @property
    def signature(self) -> Optional[Tuple[str, Set[str]]]:
        """
        Get this Command's signature -- a tuple of the name and bound parameter names.
        :return:
        """
        # Return nothing for uninitialized commands.
        if self.name is None or not self.template:
            return None

        params = set()
        for template in self.template:
            params = params.union(template.bindings)

        return self.name, params

    def __str__(self):
        return f'<command {self.name} -> {self.bound_params}/>'

    def __repr__(self):
        return self.__str__()

    def dump(self) -> str:
        """
        :return: A string representation of the underlying templates.
        """
        result = f'<command {self.name}>\n'
        for t in self.template:
            result += t.pretty_format()

        return result + '</command>'


class TemplateManager:
    """
    Handle loading, validating, and pattern matching for Command Templates.
    """
    # TODO: As it stands, all templates must be in a single file. However, given the ID->from_ID system, there is
    # TODO: nothing stopping an expansion to a directory with multiple files for ultimate modularity.
    # TODO: Gotta look into that if I get the time.

    def __init__(self, template_source: str):
        """
        Initialize this manager with a file of Templates.
        :param template_source: A file or directory containing a series of command template definitions.
        """
        source_files = []
        if isfile(template_source):
            source_files.append(template_source)
        elif isdir(template_source):
            # Supply the directory name as a prefix
            source_files.extend(join(template_source, f) for f in listdir(template_source))
        else:
            raise ValueError(f'Invalid template source {template_source}')

        self._unresolved_comps = {}  # type: Dict[str: LogicalForm.Component]
        self._parsed_commands = {}  # type: Dict[str: Command]

        # For each template source file:
        for f in source_files:
            with open(f, 'r') as fp:
                bs = BeautifulSoup(fp, 'xml')

            # Expected structure is a root <commands> tag followed by a series of <command> and <component> definitions.
            root = bs.find('commands')
            if root is None:
                raise CommandTemplateError('Missing root <commands> tag.')

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

    @property
    def command_signatures(self) -> Dict[str, Set[str]]:
        """
        Iterate over a list of command names and bound arguments within this manager.
        :return:
        """
        return {comm.name: comm.signature[1] for comm in self._parsed_commands.values()}

    def match(self, lf: LogicalForm) -> Optional[Command]:
        """
        Given a Logical Form of a sentence, match it against this manager's template library. If a command is matched
        successfully, return it.
        # TODO: Is there any value in allowing "fuzzy" matching for command that match 90% or something like that?
        :param lf: The logicalForm of a sentence.
        :return: A Command if one was matched.
        """
        # In essence, a LogicalForm is a tree. Each Component node may have N rolegroup children, each one represening
        # a set of AND clauses. Each role node must contain at leas one component, all components being an OR clause.
        for _, c in self._parsed_commands.items():
            for c_lf in c.template:
                is_match, params = lf.match_template(c_lf)
                if is_match:
                    c.bound_params = params
                    return c

        # If we checked all the options under this command and nothing matched, then there is no match.
        return None

    def dump(self) -> str:
        """
        :return: Return a string representation of this library.
        """
        result = ''
        for c in self._parsed_commands.values():
            result += c.dump()
        return result


# If running in script mode, get the source file as command line arg.
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("templates", help="A file or directory with a series of <command> and <component> definitions.")
    arg_parser.add_argument("sentence", help="A sentence to be matched against the templates.")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Enables additional output.")
    args = arg_parser.parse_args()

    # This is not meant to be a dependency of TemplateManager for the sake of decoupling, but it is useful to be able to
    # exercise the manager if command line mode.
    from parser import TripsAPI

    tm = TemplateManager(args.templates)
    api = TripsAPI()

    result = api.parse(args.sentence)
    if args.verbose:
        print(f'Input sentence parses to:\n{result.pretty_format()}')

    # Check if any template from the library matches this command.
    match = tm.match(result)

    print('\nTemplate matching result:')
    if match is None:
        print('\tNO MATCH')
    else:
        print(f'\t{match.name}')
        if args.verbose:
            print(match.bound_params)

