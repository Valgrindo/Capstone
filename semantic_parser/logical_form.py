"""
A class hierarchy for a compact and simplified AMR Logical Form representation.

:author: Sergey Goldobin
:date: 06/09/2020

CS 788.01 MS Capstone Project
"""
from typing import *
from bs4 import BeautifulSoup
from bs4 import NavigableString, Tag


class CommandTemplateError(Exception):
    """
    A simple wrapper for exceptions caused by bad command template formatting.
    """
    pass


# TODO: Move to utilities?
def compose(f: Callable, g: Callable) -> Callable:
    """
    Classic function composition from functional programming.
    compose(f, g) := f.g
    :param f: An arbitrary pure function.
    :param g: An arbitrary pure function.
    :return:
    """
    return lambda x: f(g(x))


class LogicalForm:
    """
    A simplified programmatic representation of the TRIPS Logical Form
    """

    class Component:
        """
        A component of the LF tree structure.
        """

        def __init__(self, comp_id: str, indicator: str = None, comp_type: str = None, word: str = None):
            """
            Create a new LF component.
            :param indicator: The kind of logical form component: SPEECHACT, F, BARE, etc.
            :param comp_type: The specific instance of the indicator, i.e. SA_REQUEST, PERSON, etc.
            :param comp_id: The ID of this component in the form V12345
            :param word: A concrete string representing this component.
            """
            # Since Components can be concrete or ambiguous, there must be room to express the ambiguity
            self.comp_id = comp_id  # Must be unique
            self.indicator = [] if not indicator else [indicator]
            self.comp_type = [] if not comp_type else [comp_type]
            self.word = [] if not word else [word]
            self.param_mapping = {}  # Storage for parameters which may be bound by some components.

            # Optionally, the component may have a set of roles.
            # SPEECHACTs have a CONTENT role, a PUT has AGENT, AFFECTED, and some more.
            self.roles = [{}]  # type: List[Dict[str: List[LogicalForm.Component]]]

        def __str__(self):
            indicators = '*' if not self.indicator else ', '.join(self.indicator)
            comp_types = '*' if not self.comp_type else ', '.join(self.comp_type)
            words = '*' if not self.word else ', '.join(self.word)
            return f'({indicators} {comp_types}{"" if self.word is None else f" {words}"})'

        def __repr__(self):
            return self.__str__()

        def __hash__(self):
            return hash(self.comp_id)

        def __eq__(self, other):
            return isinstance(other, LogicalForm.Component) and self.comp_id == other.comp_id

    __component_id = 0

    """
    End of nested class declarations
    """
    def __init__(self, xml_str: str = None, template_str: str = None):
        """
        Given an XML TRIPS parser output or a TRIPS template, process it into a convenient object.
        One of the two strings is required, but not both.
        :param xml_str: The TRIPS parser output.
        :param template_str: The command template string.
        """
        if (xml_str and template_str) or (not xml_str and not template_str):
            raise ValueError("Expected either XML string or template string, but not both.")

        # Root is the start of the hierarchy of Components
        self._root = None  # type: Union[LogicalForm.Component, None]
        self._raw_data = xml_str if xml_str else template_str

        if xml_str:
            self._root = LogicalForm._process_xml(xml_str)
        else:
            self._root = LogicalForm._process_template(template_str)

    """
    Pretty Printing functionality
    """
    def pretty_format(self) -> str:
        """
        Construct a pretty string representing the Logical Form
        :return:
        """
        return LogicalForm.__format_component(self._root, 0, set())

    @staticmethod
    def __format_role(role: Tuple[str, List[Component]], depth: int, seen: Set[Component]) -> str:
        role_name, role_comps = role
        result = ('|  ' * depth) + role_name + '->\n'
        for c in role_comps:
            if isinstance(c, str):
                result += ('|  ' * depth) + c + '\n'
            else:
                result += ('|  ' * depth) + LogicalForm.__format_component(c, depth + 1, seen)

        return result

    @staticmethod
    def __format_component(comp: Component, depth: int, seen: Set[Component]) -> str:
        if comp in seen:
            return ''

        seen.add(comp)
        result = ('|  ' * depth) + str(comp) + '\n'
        for rg in comp.roles:

            result += ('|  ' * depth) + '<rolegroup>\n'
            for rtup in rg.items():
                result += ('|  ' * depth) + LogicalForm.__format_role(rtup, depth + 2, seen)
            result += ('|  ' * depth) + '</rolegroup>\n'

        return result

    """
    String Parsing
    """
    @staticmethod
    def _next_id():
        """
        Components not explicitly Id'd by a programmer need an ID, and this generates a unique one.
        :return:
        """
        LogicalForm.__component_id -= 1
        return LogicalForm.__component_id

    @staticmethod
    def _process_template(template_str: str) -> Component:
        """
        Convert an XML Command template to logical Form. The command templates contain branching options for component
        structure, which is captured by this function.
        Detailed documentation on the command template format is available here: TODO: Supply link
        :param template_str: The template encoded string.
        :return: A root component of the hierarchy.
        """
        bs = BeautifulSoup(template_str, 'xml')

        command_root = bs.find('component')  # Find the root <component> tag.
        return LogicalForm.__parse_component(command_root)

    @staticmethod
    def __parse_role(root: Tag) -> Tuple[str, List[Component]]:
        """
        Parse a role tag into a mapping of its name to candidate component list.
        :param root: The root <role> node.
        :return: A <role> tuple.
        """
        if root.name != 'role':
            raise CommandTemplateError(f'Unexpected tag {root.name} instead of <role>')

        if 'name' not in root.attrs:
            raise CommandTemplateError('Role missing required "name" attribute')

        role_name = root.attrs['name'].upper()

        # A role may contain one or more expected components, parsed recursively.
        # No components indicates a wildcard accepting anything.
        components = []  # type: List[LogicalForm.Component]

        for child in root.children:
            components.append(LogicalForm.__parse_component(child))

        return role_name, components

    @staticmethod
    def __parse_component(root: Tag) -> Component:
        """
        Given a root BS4 tag of a Component, parse it into an object.
        :param root: A Tag representation from BeautifulSoup
        :return: A Component instance.
        """
        # TODO: For extra validation, implement a check for illegal of malformed tags.
        if root.name != 'component':
            raise CommandTemplateError(f'Unexpected tag {root.name} instead of <component>')

        if 'from_id' in root.attrs:
            # The presence of this attribute indicates that the component is defined elsewhere.
            # Store the ID reference to be filled in externally.
            return LogicalForm.Component(root.attrs['from_id'])

        if 'id' in root.attrs:
            # If a programmer supplied an ID, it cannot be a negative number.
            # Everything else is allowed.
            comp_id = root.attrs['id']
            try:
                val = int(comp_id)
                if val < 0:
                    raise CommandTemplateError(f'Negative number {val} is an invalid <component> id.')
            except ValueError:
                pass  # Non-numeric IDs are allowed.
        else:
            # If the programmer did not supply an id, generate a unique one.
            comp_id = LogicalForm._next_id()

        # Generate the baseline component, then fill it in based on supplied attributes and children.
        cmp = LogicalForm.Component(comp_id)

        # This attribute indicates that the words within this component will serve as parameters
        # further in the pipeline. Initialize them in storage.
        if 'map_param' in root.attrs:
            params = map(str.strip, root.attrs['map_param'].split(','))
            for p in params:
                cmp.param_mapping[p] = None  # Values get filled in during template matching.

        # If any of the following 3 attributes are populated, then those specific values are expected of the template.
        # Otherwise, component lists are left empty to signal a wildcard.
        if 'indicator' in root.attrs:
            cmp.indicator = list(map(compose(str.upper, str.strip), root.attrs['indicator'].split(',')))

        if 'type' in root.attrs:
            cmp.comp_type = list(map(compose(str.upper, str.strip), root.attrs['type'].split(',')))

        if 'word' in root.attrs:
            cmp.word = list(map(compose(str.upper, str.strip), root.attrs['word'].split(',')))

        # Finally, handle the component's children.
        # The only acceptable children are <role> and <rolegroup> tags.
        # <rolegroup> tags are OR clauses for possible role combinations on the component.
        # <role> tags within a <rolegroup> are AND clauses for the component combination.
        # For syntactic simplicity, a <component> can have only <role>s with no <rolegroup>

        # If the component has no children, we are done.
        if not root.children:
            return cmp

        first_name = root.children[0].name
        if not all(child.name == first_name for child in root.children):
            raise CommandTemplateError(f'Role mismatch: Expected either all <rolegroup> or all <role>')

        roleset = 0
        for child in root.children:
            if child.name == 'rolegroup':
                if len(child.children) == 0:
                    raise CommandTemplateError('A <rolegroup> cannot be empty.')

                # Found the next rolegroup. Advance the index and parse all component roles.
                roleset += 1
                roleset_dict = dict([LogicalForm.__parse_role(r) for r in child.children])
                cmp.roles[roleset] = roleset_dict
            elif child.name == 'role':
                rkey, rval = LogicalForm.__parse_role(child)
                cmp.roles[roleset][rkey] = rval
            else:
                raise CommandTemplateError(f'Unexpected tag {root.name} instead of <role> or <rolegroup>')

        # Unless there were exceptions, the component is parsed to completion.
        return cmp

    @staticmethod
    def _process_xml(xml_string) -> Component:
        """
        Convert an XML string to a Logical Form.
        :param xml_string: The LF encoded string.
        :return: A root component of the hierarchy.
        """
        bs = BeautifulSoup(xml_string, 'xml')
        components = {}  # type: Dict[str: LogicalForm.Component]

        comp_data = bs.findAll('rdf:Description')

        # First, we need to build up a set of standalone elements with pending ID references.
        # Then, a second pass "marries" the elements into a tree.
        root_id = comp_data[0]['rdf:ID']

        # For each component, extract its indicator, type, and -- if applicable -- word and roles.
        for tags in comp_data:
            component = LogicalForm.Component(tags['rdf:ID'])
            for c in tags.children:
                # Skip meaningless entries.
                if isinstance(c, NavigableString):
                    continue
                if c.name == 'indicator':
                    component.indicator.append(c.text)
                elif c.name == 'type':
                    component.comp_type.append(c.text)
                elif c.name == 'word':
                    component.word.append(c.text)
                elif c.prefix == 'role':
                    # Initialize the list if necessary
                    if c.name not in component.roles[0]:
                        component.roles[0][c.name] = []

                    if 'rdf:resource' in c.attrs:
                        role_comp_id = c['rdf:resource']  # Skip the 'V' prefix if needed
                        # Wrap in a list to allow isinstance() differentiation
                        component.roles[0][c.name].append([role_comp_id])
                    else:
                        # Some roles are basic strings and can be resolved on first pass.
                        component.roles[0][c.name].append(c.text)
            components[component.comp_id] = component

        # All components have been processed. Now, they need to be connected into a tree.
        for comp in components.values():
            for rname, rval in comp.roles[0].items():
                # Only resolve the roles that were left as references.
                resolved_targets = []
                for r_target in rval:
                    if isinstance(r_target, list):
                        resolved_targets.append(components[r_target[0][1:]])
                    else:
                        resolved_targets.append(r_target)
                comp.roles[0][rname] = resolved_targets

        # All components are now connected into a tree structure in memory.
        # Returning a reference to the root component therefore extracts the whole structure.
        return components[root_id]




