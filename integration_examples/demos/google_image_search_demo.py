"""
A demo of VCF integration into the Google Image Search library.

:author: Sergey Goldobin
:date: 07/22/2020 16:05
"""

from google_images_search_vc import GoogleImagesSearch
from os.path import dirname
import sys
import subprocess
import webbrowser
from enum import Enum

API_KEY = "YOUR_API_KEY"
ENGINE_ID = "YOUR_ENGINE_ID"

# Default image viewer for different platforms
IMG_VIEWER = {
    'linux': 'xdg-open',
    'win32': 'explorer',
    'darwin': 'open'
}

class DisplayMode(Enum):
    WEB = 0,
    FILE = 1


def display_results(gis: GoogleImagesSearch, mode: DisplayMode):
    """
    Show the outcome of the search to the user.
    :param gis: The GoogleImageSearch object with results populated.
    :param mode: Display results in the web browser of file explorer?
    :return:
    """
    for image in gis.results():
        if mode is DisplayMode.WEB:
            webbrowser.open(image.url, new=2)
        elif mode is DisplayMode.FILE:
            viewer = IMG_VIEWER[sys.platform]
            subprocess.run([viewer, image.path])


def run(enable_vc: bool = False):
    """
    The Image Search demo is a REPL of requests to either view or download images matching a certain query.
    :param enable_vc: True if the library should utilize Voice Controls, false otherwise.
    :return: None
    """
    print(f'Google-Image-Search demo. VC: {enable_vc}')

    print('Commands:\n'
          '\tShow me <query>\t\tFinds a set of images matching the query\n'
          '\tDownload <query>\tDownloads a set of images matching the query to the demo directory\n'
          '\tCTRL-D\t\t\t\tExit')

    gis = GoogleImagesSearch(API_KEY, ENGINE_ID)
    search_params = {  # A set of default parameters.
        'q': '',
        'num': 5,
        'safe': 'high',
        'fileType': 'jpg',
        'imgType': 'photo',
        'imgSize': 'LARGE',
        'imgDominantColor': 'black'
    }
    current_dir = dirname(__file__)

    while True:
        print('> ', end='')
        if not enable_vc:
            # If VC is disabled, take user input from the console.
            command = ''
            try:
                command = input()
            except EOFError:
                print('Shutting down...')
                exit(0)

            tokens = list(map(str.lower, command.split(' ')))
            if not tokens or len(tokens) < 2 or tokens[0] not in ['show', 'download']:
                print(f'Invalid command: {command}')
                continue
            if tokens[0].lower() == 'show' and tokens[1] != 'me':
                print(f'Invalid command: {command}')
                continue

            query = ' '.join(tokens[2:] if tokens[0] == 'show' else tokens[1:])
            search_params['q'] = query

            if tokens[0] == 'show':
                gis.search(search_params, use_vc=False)
                display_results(gis, DisplayMode.WEB)
            else:
                # 'download'
                gis.search(search_params, path_to_dir=current_dir, use_vc=False)
                display_results(gis, DisplayMode.FILE)

        else:
            # If VC is enabled, then the library will handle everything. Provide just the loop and result display.
            # TODO: Implement
            gis.search(search_params, use_vc=True)


