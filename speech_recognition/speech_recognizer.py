"""
This program utilizes Google's Speech API to gather a voice sample from the device microphone
and convert it to text.

@author Sergey Goldobin
@date 05/22/2020 16:01

CS 788.01 MS Capstone Project
"""
import msvcrt
from typing import *
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from os import environ
from io import open
import uuid
import os
import os.path
from time import time
from shutil import rmtree
import keyboard

import pyaudio
import wave
from pydub import AudioSegment

DEFAULT_LISTEN_TIME = 3  # 3 seconds. TODO: Move to a dedicated Configs file?
SERVICE_ACCOUNT_JSON = "GOOGLE_APPLICATION_CREDENTIALS"
RECORDING_BUFFER_NAME = "Recording"
DEFAULT_TIMEOUT = 10  # Seconds

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"


class KeyDisabler:
    """
    A small helper class that can temporarily disable a keyboard key.
    """

    def start(self):
        self.on = True

    def stop(self):
        self.on = False

    def __call__(self):
        while self.on:
            res = msvcrt.getwch()
            x = 0

    def __init__(self, key: str):
        self.on = False
        self.target = key


def listen(until: Callable[[], bool], timeout: int = DEFAULT_TIMEOUT):
    """
    Listen to a voice sample from device microphone and convert to text.
    :param timeout: Recording timeout boundary.
    :param until: A function that tests whether to stop recording.
    :return: str Recognized text.
    """
    # First, start recording.
    p = pyaudio.PyAudio()  # Create the audio stream.
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []  # Audio frame storage
    start_time = time()
    while not until():
        data = stream.read(CHUNK)
        frames.append(data)
        now = time()
        if (now - start_time) > timeout:
            print(' Recording timeout.')
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Create a unique temp directory and save the file there.
    tmp_dir_name = str(uuid.uuid1())
    full_path = f'{tmp_dir_name}\\{RECORDING_BUFFER_NAME}.mp3'
    if not os.path.exists(tmp_dir_name):
        os.mkdir(tmp_dir_name)

        wf = wave.open(full_path.replace('.mp3', '.wav'), 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
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
    client = speech_v1p1beta1.SpeechClient.from_service_account_json(environ.get(SERVICE_ACCOUNT_JSON))

    # The language of the supplied audio
    language_code = "en-US"  # TODO: Make language configurable

    # Sample rate in Hertz of the audio data sent
    sample_rate_hertz = 44100  # TODO: Make configurable.

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    encoding = enums.RecognitionConfig.AudioEncoding.MP3
    config = {
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
    }
    with open(full_path, "rb") as f:
        content = f.read()
    audio = {"content": content}

    response = client.recognize(config, audio)

    # TODO: Check that response was not an error.
    # Finally, clean up the temp directory.
    del audio, config, encoding, client

    rmtree(tmp_dir_name)

    return response


if __name__ == '__main__':
    print(f'Press SPACEBAR to begin recording or ENTER to exit.\n> ', end='')
    #disabler = KeyDisabler('space')
    while True:
        try:
            if keyboard.is_pressed('enter'):
                print('Exiting...')
                break
            elif keyboard.is_pressed('space'):
                #disabler.start()
                until = lambda: not keyboard.is_pressed('space')
                print('Recording...', end='')
                try:
                    text = listen(until)
                    print(text)
                except Exception as e:
                    print(f'Recognition error: {e}')

                print(' Done!')
                print('> ', end='')
                #disabler.stop()
        except:
            continue  # User pressed an unrelated key.

    exit(0)

