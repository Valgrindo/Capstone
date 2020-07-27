from __future__ import annotations
"""
This program utilizes Google's Speech API to gather a voice sample from the device microphone
and convert it to text.

@author Sergey Goldobin
@date 05/22/2020 16:01

CS 788.01 MS Capstone Project
"""
import os
import os.path
from io import open
import uuid
from time import time
from shutil import rmtree
import keyboard
import json
from queue import Queue
from collections import namedtuple
from logging import debug
from os.path import dirname, join

from framework.speech_recognition.until import Until, RecordStatus
from google.cloud.speech_v1 import enums

import soundfile as sf
import sounddevice as sd

import requests
import base64

DEFAULT_CONFIG_NAME = join(dirname(__file__), 'configuration.json')


class SpeechTranscriber:
    """
    A mechanism for recording a user's voice and converting it to text.
    """

    __audio_encodings = {
        'linear16': enums.RecognitionConfig.AudioEncoding.LINEAR16
        # TODO: More?
    }

    def __init__(self, configuration: str = None):
        """
        Initialize the transcriber.
        :param configuration: A JSON configuration file. Defaults to 'configuration.json'
        """
        if configuration is None:
            configuration = DEFAULT_CONFIG_NAME
        try:
            with open(configuration, 'r') as config_fp:
                conf_obj = json.loads(config_fp.read())
                if conf_obj["config_target"] != self.__class__.__name__:
                    raise ValueError("Configuration target mismatch.")

                # Assign all the properties from configuration.
                self.default_listen_time = conf_obj["default_listen_time"]
                self.url = conf_obj["URL"]

                self._authentication = namedtuple('authentication', ['service_account_var', 'api_key'])
                self._authentication.api_key = conf_obj["authentication"]['API_KEY']
                if not self._authentication.api_key:
                    raise ValueError('Missing Google Cloud Speech-to-Text API Key. Please see framework tutorial for '
                                     'details.')

                self._recording = namedtuple('recording', ['default_timeout', 'chunk', 'format', 'format_name',
                                                           'channels', 'rate', 'wave_filename', 'buffer_name'])
                self._recording.default_timeout = conf_obj['recording']['default_timeout']
                self._recording.chunk = conf_obj['recording']['chunk']
                self._recording.channels = conf_obj['recording']['channels']
                self._recording.rate = conf_obj['recording']['rate']
                self._recording.wave_filename = conf_obj['recording']['wave_filename']
                self._recording.buffer_name = conf_obj['recording']['buffer_name']

                self._transcription = namedtuple('transcription', ['language', 'encoding', 'encoding_name'])
                self._transcription.language = conf_obj['transcription']['language']
                self._transcription.encoding_name = conf_obj['transcription']['encoding']
                self._transcription.encoding = SpeechTranscriber.__audio_encodings[conf_obj['transcription']['encoding']]

                self._audio_data = Queue()
        except FileNotFoundError:
            print(f'File {configuration} not found.')
        except json.JSONDecodeError:
            print(f'Configuration file was malformed.')
        except KeyError as ke:
            print(f'Missing required configuration parameter: {ke}')

    def _audio_callback(self, indata, frames, time, status):
        """
        A function called by the recording library
        """
        self._audio_data.put(indata.copy())

    def listen(self, until: Until):
        """
        Record the system's audio until a condition is met and transcribe the voice.
        :param until: A function that takes no arguments and returns a boolean.
        :return: (str) A transcription of the audio.
        """
        debug('Awaiting recording.')
        start_time = time()  # Default timeout timer

        while until() == RecordStatus.AWAIT:
            now = time()
            # Wait until we are clear to begin recording.
            # It the wait it too long, throw an error.
            if (now - start_time) > self._recording.default_timeout:
                debug('Recording timeout while AWAIT')
                raise ValueError(f'Recording timeout while AWAIT')

        debug('Begin recording.')

        # Create a unique temp directory and save the file there.
        tmp_dir_name = str(uuid.uuid1())
        full_path = f'{tmp_dir_name}\\{self._recording.buffer_name}.wav'
        if not os.path.exists(tmp_dir_name):
            os.mkdir(tmp_dir_name)
            # Open an intermediate file for recording storage.
            with sf.SoundFile(full_path,
                              mode='x',
                              samplerate=self._recording.rate,
                              channels=self._recording.channels,
                              subtype="PCM_16"
                              ) as file:
                # Create an input stream on the default device.
                with sd.InputStream(samplerate=self._recording.rate,
                                    channels=self._recording.channels,
                                    callback=self._audio_callback):
                    # Continue recording while the Until condition holds.
                    while until() == RecordStatus.RECORD:
                        chunk = self._audio_data.get()
                        file.write(chunk)
                        now = time()
                        if (now - start_time) > self._recording.default_timeout:
                            debug('Recording timeout.')
                            break
        else:
            raise SystemError('Failed to generate a unique work directory.')
        debug('Recording over!')

        config = {
            "language_code": self._transcription.language,
            "sample_rate_hertz": self._recording.rate,
            "encoding": self._transcription.encoding,
        }
        with open(full_path, "rb") as f:
            content = f.read()

        content_str = base64.b64encode(content).decode('utf-8')
        data = {'config': config, 'audio': {'content': content_str}}

        response = requests.post(f'{self.url}?key={self._authentication.api_key}', data=json.dumps(data))
        result = json.loads(response.text)

        # TODO: Check that response was not an error.

        # Finally, clean up the temp directory.
        del config
        rmtree(tmp_dir_name)

        return result['results'][0]['alternatives'][0]['transcript']


if __name__ == '__main__':
    st = SpeechTranscriber()  # Initialize and parse configuration
    print(f'Press SPACEBAR to begin a {st.default_listen_time}s recording or ENTER to exit.\n> ', end='')
    while True:
        try:
            if keyboard.is_pressed('enter'):
                print('Exiting...')
                break
            elif keyboard.is_pressed('space'):
                print('Recording... ', end='')
                try:
                    text = st.listen(Until.time_expires(3))
                    print('Done!')
                    print(text)
                except Exception as e:
                    print(f'Recognition error: {e}')

                print('> ', end='')
        except:
            continue  # User pressed an unrelated key.

    exit(0)
