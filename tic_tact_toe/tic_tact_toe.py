"""
A simple implementation for a game of tic tac toe.
Used as "target practice" for the VC integration framework.

@author Sergey Goldobin
@date 05/31/2020 13:09
"""


from board import Board, GamePiece, GameStatus
from player import Player, Bot

from framework.pipeline import Pipeline
from framework.until import Until

AWAIT_COMMAND = "Awaiting command..."


def main():
    print("\nWelcome to Tic Tac Toe!\n"
          "Recognized voice commands:\n"
          "\tNew game -- restarts the game\n"
          "\tExit     -- shuts down the program\n\n"
          "During a game, you can make plays by stating the position to fill with your piece.\n"
          "\tUse {left | center | right} to refer to columns\n"
          "\tUse {top | center | bottom} to refer to rows\n"
          "\t Center tile can just eb called 'center'\n\n"
          f"For all verbal commands, press and hold SPACE when you see '{AWAIT_COMMAND}'")

    pipeline = Pipeline.get_pipeline()
    players = None
    while True:
        print(f'> Play single-player or multi-player?\n{AWAIT_COMMAND}')
        success, utt, players = pipeline.listen(Until.press_and_release('space'), for_command='GAME_MODE')
        print(f'\nYou said: {utt}')
        if not success:
            print(f'Command not recognized.')
            continue
        if players is None or 'number' not in players:
            print('There was an error processing your command. Try again.')
            continue

        if players['number'] == 'single':
            print('You chose single-player!')
        else:
            print('You chose multi-player')

        break

    players = [Player(name='Player 1', piece=GamePiece.CROSS)]
    if players == 1:
        players.append(Bot(name='AI', piece=GamePiece.CIRCLE))
    else:
        players.append(Player(name='Player 2', piece=GamePiece.CIRCLE))

    turn = 0
    board = Board()
    while True:
        print(board)  # Display board
        curr_player = players[turn]

        # Request a move and apply it
        try:
            curr_player.take_turn(board)
        except ValueError:
            continue  # Re-try a move

        status = board.get_game_status()
        if status == GameStatus.WIN:
            print(board)
            print(f'Congratulations! {curr_player} is a winner!')
            break
        elif status == GameStatus.TIE:
            print('The game is a tie!')
            break
        turn = (turn + 1) % 2


def replay():
    """
    Restart the game.
    :return:
    """
    main()


def game_over():
    """
    Abruptly end the game.
    :return:
    """
    print('\nGoodbye!')
    exit(1)


if __name__ == '__main__':
    main()
