
#create a tic toe game
def create_game():
    game = [[' ',' ',' '],[' ',' ',' '],[' ',' ',' ']]
    return game #returns the game

#print the game
def print_game(game):
    for row in game:
        print(row)

#check if the game is over
def game_over(game):
    for row in game:
        if ' ' in row:
            return False
    return True



#check if the game is over
def check_winner(game):
    #check rows
    for row in game:
        if row[0] == row[1] == row[2] != ' ':
            return True

    #check columns
    for i in range(3):
        if game[0][i] == game[1][i] == game[2][i] != ' ':
            return True

    #check diagonals
    if game[0][0] == game[1][1] == game[2][2] != ' ':
        return True
    if game[0][2] == game[1][1] == game[2][0] != ' ':
        return True
    return False


def play_game():
    game = create_game()
    print_game(game)
    while not game_over(game):
        player_move(game)
        print_game(game)
    if check_winner(game):
        print("You win!")
    else:
        print("You lose!")


def player_move(game):
    # get player move
    while True:
        try:
            row = int(input("Enter a row: "))
            col = int(input("Enter a column: "))
            if game[row][col] == ' ':
                game[row][col] = 'X'
                break
            else:
                print("That space is already taken.")
        except:
            print("Invalid move.")

    # check if game is over
    if game_over(game):
        print_game(game)
        print("Game over.")
        return

    # computer move








