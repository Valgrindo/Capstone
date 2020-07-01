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
import importlib.util
import inspect
from logging import debug
from importlib import import_module

from semantic_tools.template_manager import TemplateManager
from semantic_tools.parser import TripsAPI
from command_dispatch.command_dispatcher import CommandDispatcher, MappingType

# The pipeline
from speech_recognition.speech_recognizer import SpeechTranscriber, Until

CONFIGURATION = "pipeline_config.json"  # Expected name and location of the config file.
CONF_TEMPLATES = "template_lib"
CONF_DISPATCH = "dispatch_map"
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

    __pipeline = None

    class __Pipeline:
        """
        Hide the implementation of the pipeline, only exposing the Singleton
        """

        def __init__(self):
            """
            Initialize all the components of the pipeline.
            """
            # First, verify that config is present.
            if not isfile(CONFIGURATION):
                raise ValueError(f'Configuration file ./{CONFIGURATION} not found.')

            with open(CONFIGURATION, 'r') as fp:
                # There will be an error if something is wrong.
                config = json.load(fp)
                validate_framework_state(config)

            # The framework is all set. Load the components.
            self._speech = SpeechTranscriber()
            self._parser = TripsAPI()
            self._tm = TemplateManager(config[CONF_TEMPLATES])
            self._cd = CommandDispatcher(config[CONF_DISPATCH])

            # Load all the required modules and store them for later reference.
            self._modules = {}
            for mod in self._cd.modules:
                self._modules[mod] = import_module(mod)

        def listen(self, until: Until, for_command: str = None) -> Tuple[bool, Union[Dict[str, str], Optional[Any]]]:
            """
            Main method of interaction exposed by the pipeline. Initiates a listening sequence with an optional
            condition, transcribes the audio, matches text to the template library, and executes an appropriate
            command.
            :param until: An Until condition for listening.
            :param for_command: A name of an expected command. In not provided, any matched command is accepted.
            :return: A boolean indicator whether any command was matched and the result of command execution.
            """
            # TODO: Since this instance is shared in the program, is there ANY point in spawning a thread
            #  for performance?
            result = None
            success = False
            try:
                # First, listen to the user's voice until the provided condition is met and transcribe it.
                utterance = self._speech.listen(until)
                debug(f'User utterance: {utterance}')

                # Next, we parse the utterance into a logical form.
                lf = self._parser.parse(utterance)

                # Next, match it against the template library
                command = self._tm.match(lf)
                debug(f'Matched command: {command.name}')

                # No command was matched.
                if command is None:
                    return success, result

                # If the programmer expects a specific command to happen, verify.
                if for_command is not None and command.name != for_command:
                    return success, result

                # This will do one of the following:
                # 1) Yield the parameters bound by a GET command
                # 2) Yield the returns of the invoked function
                # 3) Raise an error indicating something bad happened.
                result = self._cd.dispatch(command, self._modules)
                success = True
            except Exception as e:
                success = False
                debug(f'Pipeline error: {e}')

            return success, result

    @staticmethod
    def get_pipeline():
        """
        Retrieve a reference to the shared Pipeline instance.
        :return: A Pipeline
        """
        if Pipeline.__pipeline is None:
            # Create the shared instance upon initialization.
            Pipeline.__pipeline = Pipeline.__Pipeline()
            return Pipeline.__pipeline
        else:
            # Return a reference to the shared instance.
            return Pipeline.__pipeline


def validate_framework_state(config: Dict[str, str]) -> bool:
    """
    Verify that the framework is functional in its current state.
    :param config: A JSON configuration object.
    :return:
    """
    # Configuration contains the template library and the dispatch mapping.
    req_keys = [CONF_TEMPLATES, CONF_DISPATCH]
    for key in req_keys:
        if key not in config:
            raise ValueError(f'Missing required {key} configuration key.')

    try:
        tm = TemplateManager(config[CONF_TEMPLATES])
        cd = CommandDispatcher(config[CONF_DISPATCH])

        # If the creation of template manager and command dispatcher succeeded, then there were no syntactic errors
        # in the files. The next step is to make sure that the methods referenced by the dispatcher exist
        # and are accessible
        for desc in cd:
            # First, we must validate that the referenced command:
            # 1) Exists
            if desc.name not in tm.command_signatures:
                raise ValueError(f'No command template named {desc.name}')

            # 2) Binds the parameters specified in the mapping.
            for arg in desc.args:
                if arg not in tm.command_signatures[desc.name]:
                    raise ValueError(f'Command template {desc.name} does not map argument "{arg}".')

            # If this is a get command, then all requirements are satisfied.
            if desc.type is MappingType.GET:
                continue

            # For INVOKE commands, validate that all required functions are accessible.
            if hasattr(desc, "module"):
                if importlib.util.find_spec(desc.module) is None:
                    raise ValueError(f'Module {desc.module} for command {desc.name} not found.')

            # TODO: It would be fairly trivial to check functions if I were to laod the module.
            # TODO: Any reason to avoid doing that?
            # Check that the module exists
            mod = importlib.import_module(desc.module)

            # if class is specified, is it present?
            if desc.class_:
                if not hasattr(mod, desc.class_):
                    raise ValueError(f'Class {desc.class_} not found in module {desc.module}.')
                func_ref = getattr(mod, desc.class_)
            else:
                func_ref = mod

            # Depending on whether class was specified,
            # target method is either a member of the class of the module.
            if not hasattr(func_ref, desc.method):
                raise ValueError(f'Method {desc.method} not found in module {desc.module}')

            # Check that the function exists within the module.
            func = getattr(func_ref, desc.method)
            if not callable(func):
                raise ValueError(f'{desc.module}.{desc.method} must be callable.')

            # Finally, check if the function actually expects the arguments specified in the description.
            spec = inspect.signature(func).parameters.copy()
            if 'self' in spec:
                del spec['self']
            if len(spec) != len(desc.args):
                raise ValueError(f'Argument count mismatch for {desc.method}: expected {len(desc.args)}, but got '
                                 f'{len(spec)}.')

            for arg in desc.args:
                if arg not in spec:
                    raise ValueError(f'Unexpected argument {arg} for {desc.method}.')

    except Exception as e:
        if isinstance(e, ValueError):
            raise e  # Simply rethrow
        raise ValueError(e)  # Rethrow wrapped as ValueError

    # If the made it to the end, then there were no problems
    return True


"""
An option to run this in script mode to validate the current configuration.
The framework folder contains a configuration file that specifies where to pull command templates and command dispatch
mappings from.
"""
if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(usage=USAGE, add_help=False)
    arg_parser.add_argument("config", help="path to pipeline configuration file.")
    arg_parser.add_argument("-v", "--validate", action="store_true",
                            help="Validate all framework components.")
    arg_parser.add_argument("-h", "--help", action="store_true",
                            help="Display a simple tutorial.")
    args = arg_parser.parse_args()

    # If neither flag was specified, there is nothing to do.
    if not (args.validate or args.help):
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
    if not isfile(args.config):
        print(f'Configuration file ./{args.config} not found.')
        exit(1)

    try:
        with open(args.config, 'r') as fp:
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

