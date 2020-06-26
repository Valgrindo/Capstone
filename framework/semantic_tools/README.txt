The semantic_tools package contains utilities that correspond to stages 2 and 3 of the voice control pipeline.

Files:

logical_form.py -- A class library for parsing Logical Form XML. Not runnable.


parse.py -- An interface to TRIPS Web API. Fully functional.
usage: parser.py [-h] text

positional arguments:
  text        Text to be semantically parsed.

optional arguments:
  -h, --help  show this help message and exit


template_manager.py -- An engine for validating and parsing command templates,as well as matching them against user
    utterances. Not fully implemented. Templates are loaded, parsed, and validated, but no matching can be done yet.
usage: template_manager.py [-h] [-v] templates sentence

positional arguments:
  templates      A file with a series of <command> and <component>
                 definitions.
  sentence       A sentence to be matched against the templates.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Enables additional output.