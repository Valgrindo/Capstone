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

from semantic_tools.template_manager import TemplateManager


XML = '.xml'
OUT = '.out'
DIR = ''

TAB_COL = 12


def run_test(source: str, exp_out: str, exp_error: bool = False) -> Tuple[bool, str, str]:
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


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("test_data", help="A directory of (#.xml, #.out) or (#, #.out) pairs with test setup "
                                              "and expected results.")
    args = arg_parser.parse_args()

    if not isdir(args.test_data):
        print(f'Error: <test_data> must be a directory.')
        exit(1)

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
        success, want, got = run_test(config, expected)
        completed.add(name)
        if success:
            print('Success.')
            test_success += 1
        else:
            print(f'Failure.\n\nEXPECTED:\n{want}\n\nGOT:\n{got}')
        test_count += 1

    proportion = (test_success / test_count) * 100
    print(f'TESTING COMPLETE! Result: ({test_success}/{test_count}) {proportion:.1f}% correct.')

