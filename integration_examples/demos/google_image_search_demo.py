"""
A demo of VCF integration into the Google Image Search library.

:author: Sergey Goldobin
:date: 07/22/2020 16:05
"""

from google_images_search_vc import GoogleImagesSearch
from os.path import dirname
import webbrowser

API_KEY = ""
ENGINE_ID = ""


def display_results(gis: GoogleImagesSearch):
    """
    Show the outcome of the search to the user.
    :param gis: The GoogleImageSearch object with results populated.
    :return:
    """
    for image in gis.results():
        if image.url:
            # If the result has a URL, then view it in a browser
            webbrowser.open(image.url, new=2)
        else:
            raise ValueError(f'No URL found for image {image}')


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
          '\tCTRL-C\t\t\t\tExit')

    if not API_KEY:
        raise ValueError('Missing API_KEY for Google Image Search API.')
    if not ENGINE_ID:
        raise ValueError('Missing ENGINE_ID for Google Image Search API.')

    gis = GoogleImagesSearch(API_KEY, ENGINE_ID)
    search_params = {  # A set of default parameters.
        'q': '',
        'num': 3,
        'safe': 'off',
        'fileType': 'jpg',
        'imgType': 'photo',
        'imgSize': 'LARGE',
        'imgDominantColor': 'white'
    }
    current_dir = dirname(__file__)

    while True:
        print('> ', end='')
        if not enable_vc:
            # If VC is disabled, take user input from the console.
            command = ''
            try:
                command = input()
            except (EOFError, KeyboardInterrupt):
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
            dir_path = None if tokens[0] == 'show' else current_dir

            # Execute the search.
            gis.search(search_params, path_to_dir=dir_path, use_vc=False)
            display_results(gis)

        else:
            # If VC is enabled, then the library will handle everything. Provide just the loop and result display.
            while True:
                input('Press ENTER to issue next command.')
                result = gis.search(search_params, use_vc=True)
                if result is not None:
                    if not result[0]:
                        print(f'\nYou said: {result[1]}\nCommand not recognized. ')
                        continue
                break
            display_results(gis)




