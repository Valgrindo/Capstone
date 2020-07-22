"""
This is a driver for examples of the Voice Control Framework (VCF) integration into third-party open source host
applications.

:author: Sergey Goldobin
:date: 07/22/2020 15:18
"""
import argparse
from demos import google_image_search_demo

# Module choices
MODULES = ["image-search"]

# Mapping of demo names to functions
DEMO_MAP = {
    "image-search": google_image_search_demo.run
}


"""
Main function. Selects and executes an appropriate demo.
"""


def main():
    argp = argparse.ArgumentParser()
    argp.add_argument('-m', '--module', help='An integrated module demo to run.', choices=MODULES, required=True)
    argp.add_argument('-no_vc', '--no_voice_control', action='store_true',
                      help='Run the demo without voice controls (base library)')
    args = argp.parse_args()

    # Execute the appropriate demo sequence.
    DEMO_MAP[args.module](enable_vc=not args.no_voice_control)


if __name__ == '__main__':
    main()
