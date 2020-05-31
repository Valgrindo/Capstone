"""
An abstraction representing a Tic Tac Toe player. Could be human or AI.

@author Sergey Goldobin
@date 05/31/2020 13:24
"""

from enum import Enum
from typing import NoReturn

from board import GamePiece, Board


class PlayerKind(Enum):
    HUMAN = 0,
    AI = 1


class Player:

    def __init__(self, name: str, piece: GamePiece):
        self.name = name
        self.piece = piece

    def __repr__(self):
        return f'{self.name}[{self.piece}]'

    def __str__(self):
        return self.__repr__()

    def take_turn(self, board: Board) -> NoReturn:
        """
        Given a board state, prompt for player input and make a move.
        :param board: The current game board state. Gets updated.
        :return: None
        """
        move = input(f'Enter a move for {self}: ')
        # TODO Add robust input validation and hints
        move = int(move[0]), int(move[1])

        if board[move] is not None:
            raise ValueError('Attempt to move on a take space.')

        board[move] = self.piece


class Bot(Player):

    def take_turn(self, board: Board) -> NoReturn:
        # TODO Implement an AI to play tic tac toe.
        pass
