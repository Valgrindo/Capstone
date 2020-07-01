"""
A simple implementation for a game of tic tac toe.
Used as "target practice" for the VC integration framework.

@author Sergey Goldobin
@date 05/31/2020 13:09
"""


from board import Board, GamePiece, GameStatus
from player import Player, Bot


def main():
    print("Welcome to Tic Tac Toe!\n"
          "Recognized voice commands:\n"
          "\tNew game -- restarts the game\n"
          "\texit     -- shuts down the program\n")
    players = input('Enter number of players {1 or 2}: ')

    try:
        players = int(players)
        if not 1 <= players <= 2:
            raise ValueError
    except ValueError:
        print(f'Invalid value {players}: Must be 1 or 2.')
        exit(1)

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


if __name__ == '__main__':
    main()
