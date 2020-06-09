"""
A class hierarchy for a compact and simplified AMR Logical Form representation.

:author: Sergey Goldobin
:date: 06/09/2020

CS 788.01 MS Capstone Project
"""
from typing import *
from bs4 import BeautifulSoup
from bs4 import NavigableString


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
            self.indicator = indicator
            self.comp_type = comp_type
            self.comp_id = comp_id
            self.word = word

            # Optionally, the component may have a set of roles.
            # SPEECHACTs have a CONTENT role, a PUT has AGENT, AFFECTED, and some more.
            self.roles = {}  # type: Dict[str: LogicalForm.Component]

        def __str__(self):
            return f'({self.indicator} {self.comp_type}{"" if self.word is None else " " + self.word})'

        def __repr__(self):
            return self.__str__()

        def __hash__(self):
            return hash(self.comp_id)

        def __eq__(self, other):
            return isinstance(other, LogicalForm.Component) and self.comp_id == other.comp_id

    class Wildcard:
        """
        A component that matches any other component.
        """

        def __str__(self):
            return "(*)"

        def __repr__(self):
            return self.__str__()

        def __eq__(self, other):
            return isinstance(other, LogicalForm.Component) or isinstance(other, LogicalForm.Wildcard)

    """
    End of nested class declarations
    """
    def __init__(self, xml_string: Union[str, None]):
        """
        Given an XML TRIPS parser output, process it into a convenient object.
        :param xml_string: The TRIPS parser output.
        """
        # Root is the start of the hierarchy of Components
        self._root = None  # type: Union[LogicalForm.Component, None]
        self._raw_data = xml_string

        if xml_string is not None:
            self._root = LogicalForm._process_xml(xml_string)

    @staticmethod
    def _process_xml(xml_string) -> Component:
        """
        Convert an XML string to a Logical Form.
        IMPORTANT: The expected XML format is modified from the original documentation at
        http://trips.ihmc.us/parser/api.html
        More details inside this function, as well as in TODO: Link external docs
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
                    component.indicator = c.text
                elif c.name == 'type':
                    component.comp_type = c.text
                elif c.name == 'word':
                    component.word = c.text
                elif c.prefix == 'role':
                    if 'rdf:resource' in c.attrs:
                        role_comp_id = c['rdf:resource']  # Skip the 'V' prefix if needed
                        # Wrap in a list to allow isinstance() differentiation
                        component.roles[c.name] = [role_comp_id]
                    else:
                        # Some roles are basic strings and can be resolved on first pass.
                        component.roles[c.name] = c.text
            components[component.comp_id] = component

        # All components have been processed. Now, they need to be connected into a tree.
        for comp in components.values():
            for rname, rval in comp.roles.items():
                # Only resolve the roles that were left as references.
                if isinstance(rval, list):
                    comp.roles[rname] = components[rval[0][1:]]

        # All components are now connected into a tree structure in memory.
        # Returning a reference to the root component therefore extracts the whole structure.
        return components[root_id]




