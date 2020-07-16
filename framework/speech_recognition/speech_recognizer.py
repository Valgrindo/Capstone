from __future__ import annotations
"""
This program utilizes Google's Speech API to gather a voice sample from the device microphone
and convert it to text.

@author Sergey Goldobin
@date 05/22/2020 16:01

CS 788.01 MS Capstone Project
"""
from typing import *
import os
import os.path
from io import open
import uuid
from time import time
from shutil import rmtree
import keyboard
import json
from collections import namedtuple
from logging import debug
from framework.until import Until
from os.path import dirname, join
from framework.until import RecordStatus

from google.cloud.speech_v1p1beta1 import enums

import pyaudio
import wave
from pydub import AudioSegment

import requests
import base64

DEFAULT_CONFIG_NAME = join(dirname(__file__), 'configuration.json')


class SpeechTranscriber:
    """
    A mechanism for recording a user's voice and converting it to text.
    """

    __audio_formats = {
        'paInt16': pyaudio.paInt16,
        # TODO: More?
    }

    __audio_encodings = {
        'mp3': enums.RecognitionConfig.AudioEncoding.MP3
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
                    raise ValueError('Missing Google Cloud Speech-to-Text API Key. Please see README for details.')

                self._recording = namedtuple('recording', ['default_timeout', 'chunk', 'format', 'channels',
                                                           'rate', 'wave_filename', 'buffer_name'])
                self._recording.default_timeout = conf_obj['recording']['default_timeout']
                self._recording.chunk = conf_obj['recording']['chunk']
                self._recording.channels = conf_obj['recording']['channels']
                self._recording.rate = conf_obj['recording']['rate']
                self._recording.wave_filename = conf_obj['recording']['wave_filename']
                self._recording.buffer_name = conf_obj['recording']['buffer_name']
                self._recording.format = conf_obj['recording']['format']
                self._recording.format = SpeechTranscriber.__audio_formats[conf_obj['recording']['format']]

                self._transcription = namedtuple('transcription', ['language', 'encoding'])
                self._transcription.language = conf_obj['transcription']['language']
                self._transcription.encoding = SpeechTranscriber.__audio_encodings[conf_obj['transcription']['encoding']]
        except FileNotFoundError:
            print(f'File {configuration} not found.')
        except json.JSONDecodeError:
            print(f'Configuration file was malformed.')
        except KeyError as ke:
            print(f'Missing required configuration parameter: {ke}')

    def listen(self, until: Until):
        """
        Record the system's audio until a condition is met and transcribe the voice.
        :param until: A function that takes no arguments and returns a boolean.
        :return: (str) A transcription of the audio.
        """

        # First, start recording.
        p = pyaudio.PyAudio()  # Create the audio stream.
        stream = p.open(format=self._recording.format,
                        channels=self._recording.channels,
                        rate=self._recording.rate,
                        input=True,
                        frames_per_buffer=self._recording.chunk)

        debug('Awaiting recording.')
        frames = []  # Audio frame storage
        start_time = time()  # Default timeout timer

        while until() is RecordStatus.AWAIT:
            now = time()
            # Wait until we are clear to begin recording.
            # It the wait it too long, throw an error.
            if (now - start_time) > self._recording.default_timeout:
                debug('Recording timeout while AWAIT')
                raise ValueError(f'Recording timeout while AWAIT')

        debug('Begin recording.')
        while until() is RecordStatus.RECORD:
            data = stream.read(self._recording.chunk)
            frames.append(data)
            now = time()
            if (now - start_time) > self._recording.default_timeout:
                debug('Recording timeout.')
                break
        debug('Recording over!')

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Create a unique temp directory and save the file there.
        tmp_dir_name = str(uuid.uuid1())
        full_path = f'{tmp_dir_name}\\{self._recording.buffer_name}.mp3'
        if not os.path.exists(tmp_dir_name):
            os.mkdir(tmp_dir_name)

            wf = wave.open(full_path.replace('.mp3', '.wav'), 'wb')
            wf.setnchannels(self._recording.channels)
            wf.setsampwidth(p.get_sample_size(self._recording.format))
            wf.setframerate(self._recording.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            del wf

            # Now, convert the Wav to MP3
            sound = AudioSegment.from_wav(full_path.replace('.mp3', '.wav'))
            sound.export(full_path, format='mp3')
            del sound
        else:
            raise SystemError('Failed to generate a unique work directory.')

        # A recording file has been saved. Now, ship it away to Google.
        # client = speech_v1p1beta1.SpeechClient.from_service_account_json(
        #     environ.get(self._authentication.service_account_var))

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

        debug(f'Recognition result: {result}')
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
                #until = Until(lambda: not keyboard.is_pressed('space'))
                print('Recording...', end='')
                try:
                    text = st.listen(Until.time_expires(3))
                    print(text)
                except Exception as e:
                    print(f'Recognition error: {e}')

                print(' Done!')
                print('> ', end='')
        except:
            continue  # User pressed an unrelated key.

    exit(0)
