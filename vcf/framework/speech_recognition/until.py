from __future__ import annotations
"""
A utility for easy pipeline listening condition specification.

:author: Sergey Goldobin
:date: 07/01/2020
"""

from typing import *
from time import time
import keyboard
from enum import Enum


class RecordStatus(Enum):
    """
    An enumeration over recording status.
    """
    AWAIT = 0,
    RECORD = 1,
    STOP = 2

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value


class Until:
    """
    An abstraction that makes it convenient to pass predicates to SpeechTranscriber listen() method.
    """

    def __init__(self, condition: Callable[[], RecordStatus]):
        self.__condition = condition

    def __call__(self, *args, **kwargs):
        return self.__condition()

    # This section contains several predicate factories for convenient use with listen()
    @staticmethod
    def time_expires(seconds: int) -> Until:
        """
        Create a predicate that 'expires' after a given number of seconds elapses.
        :param seconds: A whole number of seconds.
        :return: An 'until' predicate
        """
        start = time()
        return Until(lambda: RecordStatus.STOP if time() - start > seconds else RecordStatus.RECORD)

    @staticmethod
    def press_and_release(key: str) -> Until:
        """
        Create a predicate that lasts until a user presses, holds, and releases a given keyboard key
        :param key:
        :return:
        """
        # TODO: Add validation that entered key is legit.
        Until._par_help.been_released = False
        Until._par_help.been_pressed = False
        return Until(lambda: Until._par_help(key))

    @staticmethod
    def _par_help(key: str) -> RecordStatus:
        is_pressed = keyboard.is_pressed(key)

        if is_pressed:
            Until._par_help.been_pressed = True
        if not is_pressed and Until._par_help.been_pressed:
            Until._par_help.been_released = True

        # If the button has not been released AND it is not pressed right now, we are waiting to start recording.
        if not Until._par_help.been_released and not is_pressed:
            return RecordStatus.AWAIT
        # If the button ahs not been released AND is is currently pressed, we are recording.
        if not Until._par_help.been_released and is_pressed:
            return RecordStatus.RECORD
        # # If the button HAS been released AND it is not pressed right now, we are done recording.
        if Until._par_help.been_released and not is_pressed:
            return RecordStatus.STOP

    # TODO Write more. Perhaps key_up() and key_down()?
