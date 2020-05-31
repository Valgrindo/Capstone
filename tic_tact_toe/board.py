"""
An abstraction representing a tic tac toe game board.

@author Sergey Goldobin
@date 05/31/2020 13:33
"""

from typing import *
from enum import Enum

BOARD_EDGE = 3


class GamePiece(Enum):
    CROSS = 'X',
    CIRCLE = 'O'

    def __str__(self):
        return self.value[0]


class GameStatus(Enum):
    WIN = 'victory',
    TIE = 'tie',
    UNDECIDED = 'undecided'


class Board:

    def __init__(self):
        # Create a squared board.
        self.__state = [[None for _ in range(0, BOARD_EDGE)] for _ in range(0, BOARD_EDGE)]

    def __getitem__(self, item: Tuple[int, int]) -> Optional[GamePiece]:
        if not isinstance(item, tuple):
            raise ValueError('Expected a tuple index of the form (row, column)')

        if not isinstance(item[0], int) or not isinstance(item[1], int):
            raise ValueError('Expected tuple indices members to be integers.')

        if not (item[0] in range(0, BOARD_EDGE) or not item[1] in range(0, BOARD_EDGE)):
            raise ValueError('Indices out of range.')

        return self.__state[item[0]][item[1]]

    def __setitem__(self, key: Tuple[int, int], value: GamePiece):
        if not isinstance(key, tuple):
            raise ValueError('Expected a tuple index of the form (row, column)')

        if not isinstance(key[0], int) or not isinstance(key[1], int):
            raise ValueError('Expected tuple indices members to be integers.')

        if not (key[0] in range(0, BOARD_EDGE) or not key[1] in range(0, BOARD_EDGE)):
            raise ValueError('Indices out of range.')

        self.__state[key[0]][key[1]] = value

    def get_game_status(self) -> GameStatus:
        """
        Tetermine if the game is still going on, or if there is a tie or a winner.
        :return: The status of the game.
        """
        horizontals = [x for x in self.__state]
        verticals = []
        for c in range(0, BOARD_EDGE):
            col = []
            for r in range(0, BOARD_EDGE):
                col.append(self[r, c])
            verticals.append(col)
        diagonals = [[(i, i) for i in range(0, BOARD_EDGE)], [(i, BOARD_EDGE - 1 - i) for i in range(0, BOARD_EDGE)]]
        for i in range(len(diagonals)):
            diagonals[i] = [self[tup] for tup in diagonals[i]]

        all_candidates = horizontals + verticals + diagonals
        tie = False
        for candidate in all_candidates:
            if candidate is None:
                tie = True
            if candidate[0] is not None and candidate.count(candidate[0]) == len(candidate):
                # Row is all the same symbol
                return GameStatus.WIN

        if tie:
            return GameStatus.TIE

        return GameStatus.UNDECIDED

    def __str__(self):
        """
        Display the game board to stdout.
        ------------
        | X | O |  |
        :return:
        """
        div = '-' * (BOARD_EDGE * 4) + '-\n'
        result = ''
        for row in self.__state:
            for p in row:
                result += f'| {" " if p is None else p} '

            result += '|\n'
            result += div

        return result



