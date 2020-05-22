"""
This program utilizes Google's Speech API to gather a voice sample from the device microphone
and convert it to text.

@author Sergey Goldobin
@date 05/22/2020 16:01

CS 788.01 MS Capstone Project
"""

from typing import *
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from os import environ
from io import open

DEFAULT_LISTEN_TIME = 3000  # 3 seconds. TODO: Move to a dedicated Configs file?
SERVICE_ACCOUNT_JSON = "GOOGLE_APPLICATION_CREDENTIALS"
DEFAULT_PATH = ".\\Recording.mp3"


def listen(duration: int):
    """
    Listen to a voice sample from device microphone and convert to text.
    :param duration: Duration of listening in milliseconds.
    :return: str Recognized text.
    """
    client = speech_v1p1beta1.SpeechClient.from_service_account_json(environ.get(SERVICE_ACCOUNT_JSON))

    storage_uri = 'gs://cloud-samples-data/speech/brooklyn_bridge.mp3'

    # The language of the supplied audio
    language_code = "en-US"

    # Sample rate in Hertz of the audio data sent
    sample_rate_hertz = 44100

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    encoding = enums.RecognitionConfig.AudioEncoding.MP3
    config = {
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
    }
    with open(DEFAULT_PATH, "rb") as f:
        content = f.read()
    audio = {"content": content}

    response = client.recognize(config, audio)
    return response


if __name__ == '__main__':
    print(f'Listening for {DEFAULT_LISTEN_TIME / 1000:0.1f} s...')
    text = listen(DEFAULT_LISTEN_TIME)
    print(f'Recognition result:\n{text}')
