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

    def __hash__(self):
        lst_hashes = []
        for c in range(0, BOARD_EDGE):
            lst_hashes.append(tuple(self.__state[c]))
        return hash(tuple(lst_hashes))

    def __eq__(self, other):
        """
        Boards are equal if all elemets are equal.
        :param other:
        :return:
        """
        if not isinstance(other, Board):
            return False
        for c in range(0, BOARD_EDGE):
            for r in range(0, BOARD_EDGE):
                if self[r, c] != other[r, c]:
                    return False

        return True

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

    def _get_lines(self):
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

        return horizontals, verticals, diagonals

    def get_game_status(self) -> GameStatus:
        """
        Tetermine if the game is still going on, or if there is a tie or a winner.
        :return: The status of the game.
        """
        horizontals, verticals, diagonals = self._get_lines()

        all_candidates = horizontals + verticals + diagonals
        tie = all(all(c) for c in all_candidates)
        if tie:
            return GameStatus.TIE

        for candidate in all_candidates:
            if candidate[0] is not None and candidate.count(candidate[0]) == len(candidate):
                # Row is all the same symbol
                return GameStatus.WIN

        return GameStatus.UNDECIDED

    def __copy__(self):
        nb = Board()
        nb.__state = [[v for v in r] for r in self.__state]

        return nb

    def __str__(self):
        """
        Display the game board to stdout.
        ------------
        | X | O |  |
        :return:
        """
        div = '-' * (BOARD_EDGE * 4) + '-\n'
        result = div
        for row in self.__state:
            for p in row:
                result += f'| {" " if p is None else p} '

            result += '|\n'
            result += div

        return result

    def get_children(self, piece: GamePiece):
        """
        Get a set of Boards that are 1 move away from this one.
        :return:
        """
        result = []

        for c in range(0, BOARD_EDGE):
            for r in range(0, BOARD_EDGE):
                tile = self[r, c]

                # Cannot spawn children from free tiles.
                if tile is not None:
                    continue

                child = self.__copy__()
                child[r, c] = piece
                result.append(child)
        return result

    def score(self, piece: GamePiece):
        """
        Move space in Tic-Tac-Toe is not very large, so a probabilistic search would guarantee perfect results while
        Not taking too long to compute. However, that's lame. Instead, I will score all board states that can be
        immediately reached from the current one and score the victory potential of each one.
        Scoring:
            Victory     30  This piece forms a triple
            Block       20  This piece blocks a pair for the opponent
            Pair        5   This piece is adjacent to another piece from same player
            Center      2   This piece occupies the center tile
            Single      1   Any other piece
        """
        score = 0
        for c in range(0, BOARD_EDGE):
            for r in range(0, BOARD_EDGE):
                tile = self[r, c]

                # The tile contributes no points if it is empty or occupied by other player.
                if (tile is None) or (tile is not None and tile is not piece):
                    continue

                # Any non-empty matching tile is a point.
                score += 1

                # 1 point for center tile.
                if (0 < c < BOARD_EDGE) and (0 < r < BOARD_EDGE):
                    score += 1

                # 5 points for a pair in any direction
                rs = [r-1, r, r+1]
                cs = [c-1, c, c+1]
                locs = []
                for row in rs:
                    for col in cs:
                        if row == r and col == c:
                            continue
                        locs.append((row, col))

                for loc in locs:
                    try:
                        neighbor = self[loc]
                        if neighbor == tile:
                            score += 5
                    except:
                        pass

        # Now, examine board lines for victory and block
        hs, vs, ds = self._get_lines()
        all_lines = hs + vs + ds

        for line in all_lines:
            # Board contains a winning combination.
            if all(x == piece for x in line):
                score += 30

            # Board contains a victory block for opponent.
            if line.count(piece) == 1 and line.count(None) == 0:
                score += 20

        return score



