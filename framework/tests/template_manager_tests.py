"""
A suite of unit tests for the TemplateManager class.

:author: Sergey Goldobin
:date: 06/18/2020 13:04
"""


import argparse
from typing import *
from os import listdir, chdir
from os.path import isdir, splitext, isfile, join
from math import floor
from enum import Enum
from json import loads

from template_manager import TemplateManager
from lf_parser import TripsAPI


class TestMode(Enum):
    """
    An enumeration for the different kinds of test modes.
    """
    PARSE = 'PARSE',
    MATCH = 'MATCH'


XML = '.xml'
OUT = '.out'
DIR = ''

TAB_COL = 12


def run_parse_test(source: str, exp_out: str, exp_error: bool = False) -> Tuple[bool, str, str]:
    """
    Given an source file or directory, parse it into a TemplateLibrary and compare it with expected output.
    :param source: A path to a file or directory.
    :param exp_out: File containing expected output.
    :param exp_error: Whether to expect the TemplateManager to throw an exception.
    :return: A tuple with a success indicator, expected output, and received output
    """
    success = False

    # Read in the expected output.
    t_fp = open(exp_out, 'r')
    target = t_fp.read()
    t_fp.close()

    try:
        tm = TemplateManager(source)
        got = tm.dump()
    except Exception as e:
        got = e.__str__()

    return target == got, target, got


def all_valid(dir_name: str) -> Tuple[bool, List[str]]:
    """
    Make sure that all test items in a given directory are valid.
    A valid test item is an XML file or a directory with an OUT file that has the same name.
    Directories must consist entirely of XML files.
    :param dir_name: The directory to test.
    :return: A tuple with a boolean success indicator and a list of violators, if applicable.
    """
    name_bank = {}  # type: Dict[str: str]
    errors = []

    for name, ext in map(splitext, listdir(dir_name)):
        # First, test the item for standalone validity
        if isdir(join(dir_name, name)):
            if any(not f.endswith('xml') for f in listdir(join(dir_name, name))):
                errors.append(f'Bad item, {name}: Invalid extension on some internal templates.')
                continue
        else:
            # Item must be incorrect if is is neither a directory nor a file with a valid extension.
            if ext not in [XML, OUT]:
                errors.append(f'Bad item {name + ext}: Invalid extension {ext}')
                continue

        # Item is internally valid. Now test for compatibility with already seen items.
        if name not in name_bank:
            name_bank[name] = ext
        elif name_bank[name] is None:
            errors.append(f'Bad item {name + ext}: Duplicate entry following a resolved pair.')
        else:
            # If the name was already seen, but the extension is the same, then this is a duplicate.
            if ext == name_bank[name]:
                errors.append(f'Bad item {name + ext}: Duplicate entry.')
                continue

            # If we have already seen a .OUT, then it must eb resolved by an XML or a directory.
            if ext not in [XML, DIR] and name_bank[name] == OUT:
                errors.append(f'Bad item {name + ext}: {name + ".xml"} or {name} directory required for {name + ".out"}')
                continue

            if ext != OUT and name_bank[name] in [XML, DIR]:
                errors.append(f'Bad item {name + ext}: {name + ".out"} required for {name + name_bank[name]}')
                continue

            # If we got here, then the item resolves the one seen before. Implicit success.
            name_bank[name] = None

    # Anything left in the name bank is not resolved.
    name_bank = dict(filter(lambda kv: kv[1] is not None, name_bank.items()))
    for key, value in name_bank.items():
        if value in [XML, DIR]:
            errors.append(f'Bad item {key + value}: Missing corresponding {key + ".out"}')
        else:
            errors.append(f'Bad item {key + value}: Missing corresponding {key + ".xml"} or {key} directory.')

    return len(errors) == 0, errors


def run_parse_tests():
    """
    Perform all the work related to running a TemplateManager parsing tests.
    :return:
    """
    # Test if the provided test files are correct.
    valid, errors = all_valid(args.test_data)
    if not valid:
        print(f'Found {len(errors)} errors with supplied files:')
        for e in errors:
            print('\t' + e)
        exit(1)

    # Switch directory for easy file lookup
    chdir('.\\' + args.test_data)

    # Clear to begin testing
    print('BEGIN TESTING:')
    test_count, test_success = 0, 0
    completed = set()  # type: Set[str]

    for item in listdir('.'):
        name, ext = splitext(item)
        if name in completed:
            continue

        expected = name + OUT
        config = name + XML if isfile(name + XML) else name + DIR

        msg = f'Running test {name} ...'
        tabs = floor(len(msg) / 4)

        print(msg, '\t' * (TAB_COL - tabs), end='')
        success, want, got = run_parse_test(config, expected)
        completed.add(name)
        if success:
            print('Success.')
            test_success += 1
        else:
            print(f'Failure.\n\nEXPECTED:\n{want}\n\nGOT:\n{got}')
        test_count += 1

    proportion = (test_success / test_count) * 100
    print(f'TESTING COMPLETE! Result: ({test_success}/{test_count}) {proportion:.1f}% correct.')


def run_match_tests():
    """
    Perform all the work related to running a TemplateManager matching tests.
    :return:
    """
    # Expected setup for this test is a collection of template libraries and sets of accepted/rejected sentences with
    # the appropriate parameter mappings.
    libraries = args.test_data

    # Test if the provided test files are correct.
    valid, errors = all_valid(libraries)
    if not valid:
        print(f'Found {len(errors)} errors with supplied files:')
        for e in errors:
            print('\t' + e)
        exit(1)

    print('BEGIN TESTING:')
    test_count, test_success = 0, 0
    completed = set()  # type: Set[str]
    api = TripsAPI()

    # Switch directory for easy file lookup
    chdir('.\\' + libraries)

    # For each pair of files, create a TemplateManager out of the XML library
    # Then, try to match all provided phrases in a .out file to expected outcomes
    for file in listdir('.'):
        name, ext = splitext(file)
        results = name + OUT

        source = name + XML
        if isdir(name):
            source = name

        if name in completed:
            continue
        completed.add(name)

        print(f'Running test group {name}:')
        # Create a manager. Expected to succeed.
        tm = TemplateManager(source)

        # Run all the subtests
        with open(results, 'r') as rfp:
            for test in rfp:
                data = test.strip().split(';')  # [Test expectation, sentence, Optional param dictionary]
                if len(data) <= 1 or len(data) >= 5:
                    print(f'\tInvalid test: {data}')
                    continue
                print(f'\t{data[1]} \t\t--> ', end='')

                result = tm.match(api.parse(data[1]))

                # If we expect no match, i.e. the flag is FALSE, the result must be None
                if (data[0].upper() == 'FALSE') and (result is None):
                    test_success += 1
                    print('Correct')
                elif data[0].upper() == 'FALSE':
                    print(f'\nEXPECTED:\n NO MATCH\n\nGOT:\n{result}')
                elif data[0].upper() == 'TRUE' and (result is None):
                    print('\nEXPECTED:\n MATCH\n\nGOT:\nNO MATCH')
                else:
                    # Expected and got a match. Must validate the argument dictionary if applicable.
                    got_params = result.bound_params
                    exp_params = loads(data[2])

                    got_groups = result.groups
                    exp_groups = loads(data[3])
                    if got_params == exp_params and got_groups == exp_groups:
                        print('Correct.')
                        test_success += 1
                    else:
                        print(f'\nEXPECTED:\n{exp_params, exp_groups}\nGOT:\n{got_params, got_groups}')

                test_count += 1
    proportion = (test_success / test_count) * 100
    print(f'TESTING COMPLETE! Result: ({test_success}/{test_count}) {proportion:.1f}% correct.')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("test_data", help="A directory of (#.xml, #.out) or (#, #.out) pairs with test setup "
                                              "and expected results.")
    arg_parser.add_argument("-m", "--mode", type=str, choices=['parse', 'match'],
                            help="Use 'parse' mode to test the TemplateManager's parsing of template libraries.\n"
                                 "Use 'match' mode to test the TemplateManager's matching of sentences to templates.\n"
                                 "Use 'all' to do both.")
    args = arg_parser.parse_args()

    if not isdir(args.test_data):
        print(f'Error: {args.test_data} is not a directory')

    # Determine what kind of tests to run.
    mode = TestMode.PARSE
    if (args.mode is not None) and (args.mode.upper() == TestMode.MATCH.name):
        mode = TestMode.MATCH

    if mode == TestMode.PARSE:
        run_parse_tests()

    if mode == TestMode.MATCH:
        run_match_tests()
