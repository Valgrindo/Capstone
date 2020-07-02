"""
An abstraction representing a Tic Tac Toe player. Could be human or AI.

@author Sergey Goldobin
@date 05/31/2020 13:24
"""

from enum import Enum
from typing import NoReturn

from board import GamePiece, Board

from framework.pipeline import Pipeline
from framework.until import Until


class PlayerKind(Enum):
    HUMAN = 0,
    AI = 1


class Player:

    row_map = {'top': 0, 'center': 1, 'middle': 1, 'bottom': 2}
    col_map = {'left': 0, 'leave': 0, 'center': 1, 'middle': 1, 'right': 2}

    def __init__(self, name: str, piece: GamePiece):
        self.name = name
        self.piece = piece
        self.pipeline = Pipeline.get_pipeline()  # Retrieve a reference to the shared pipeline instance

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
        print(f'> Move for {self}. Press and hold SPACE to record when ready.')
        while True:
            print('Awaiting command...')
            success, utt, move_data = self.pipeline.listen(until=Until.press_and_release('space'))
            print(f'\n\tYou said: {utt}')
            if not success:
                print(f'\tYour command was not recognized. Please, try again.')
                continue

            # If the user issued a bad command, inform them and retry.
            if (move_data is None) or ('row' not in move_data) or ('col' not in move_data):
                print('\tUnexpected error processing your command. Please, try again.')
            else:
                move_loc = move_data['row'].lower(), move_data['col'].lower()
                print(f'\tYour move: {move_loc[0]} row, {move_loc[1]} column')
                to_apply = Player.row_map[move_loc[0]], Player.col_map[move_loc[1]]

                if board[to_apply] is not None:
                    print('\tAttempt to move on a taken space. Try again.')
                    continue
                # Move was valid. Apply it.
                board[to_apply] = self.piece
                break


class Bot(Player):

    def take_turn(self, board: Board) -> NoReturn:
        # TODO Implement an AI to play tic tac toe.
        pass
