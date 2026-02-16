from flask import Flask, render_template, request, redirect, session, abort, url_for
import secrets
import threading
app = Flask(__name__)
app.secret_key = "super-duper-secret"

games = {}
games_lock = threading.Lock()

winningLines = [[(0, 0), (0, 1), (0, 2)],
                [(1, 0), (1, 1), (1, 2)],
                [(2, 0), (2, 1), (2, 2)],

                [(0, 0), (1, 0), (2, 0)],
                [(0, 1), (1, 1), (2, 1)],
                [(0, 2), (1, 2), (2, 2)],

                [(0, 0), (1, 1), (2, 2)],
                [(2, 0), (1, 1), (0, 2)],
                ]

def initGame():
    
    return {
        "board": [[" ", " ", " "],
                [" ", " ", " "],
                [" ", " ", " "],
                ],
        "players": [],
        "turn":0,
        "winner":-1
    }
    # -1 = game ongoing
    #  0 = player 0 wins
    #  1 = player 1 wins
    # -2 = draw


def checkWinner(board):
    for line in winningLines:
        values = []
        for r,c in line:
            values.append(board[r][c])
            if values == ["X", "X", "X"]:
                return 0
            elif values == ["O", "O", "O"]:
                return 1
            
    for r in board:
        for c in r:
            if c == " ":
                return -1
    return -2

@app.route("/create")
def create():
    game_id = secrets.token_urlsafe(6)
    with games_lock:
        games[game_id] = initGame()
    return redirect(url_for('game', game_id=game_id))

@app.route("/game/<game_id>")
def game(game_id):
    if game_id not in games:
        abort(404)
    game = games[game_id]
    player_token = session.get(f"player_{game_id}")
    player_index = None
    if player_token and player_token in game["players"]:
        player_index = game["players"].index(player_token)
    return render_template("game.html",
                           game_id=game_id,
                           board = game["board"],
                           turn = game["turn"],
                           winner = game["winner"],
                           player_index = player_index,
                           player_count = len(game["players"])
                           )


@app.route("/join/<game_id>", methods=["POST"])
def join(game_id):
    if game_id not in games:
        abort(404)

    with games_lock:
        game = games[game_id]
        if len(game["players"]) >= 2:
            return "Game is full :(", 400
        token = secrets.token_urlsafe(8)
        game["players"].append(token)
        session[f"player_{game_id}"] = token
    return redirect(url_for('game', game_id=game_id))
        


@app.route("/move/<game_id>", methods=["POST"])
def move(game_id):
    
    if game_id not in games:
        abort(404)

    row = int(request.form["row"])
    column = int(request.form["column"])
    
    token = session.get(f"player_{game_id}")
    if not token:
        return "You are not the player in this game. Join first", 403

    with games_lock:
        game = games[game_id]
        if token not in game["players"]:
            return "Not participating", 403
        player_index = game["players"].index(token)

        if game["winner"] != -1:
            return redirect(url_for('game', game_id=game_id))
        if player_index != game["turn"]:
            return "Not your turn", 403
        if game["board"][row][column] != " ":
            return "Cell not empty", 400
        
        game["board"][row][column] = "X" if player_index == 0 else "O"

        game["winner"] = checkWinner(game["board"])

        if game["winner"] == -1:
            game["turn"] = 1- game["turn"]
        return redirect(url_for('game', game_id = game_id))

@app.route("/reset/<game_id>", methods=["POST"])
def reset(game_id):
    if game_id not in games:
        return abort(404)
    with games_lock:
        games[game_id] = initGame()
    
    return redirect(url_for('game', game_id=game_id))

app.run(debug=True, port=5001)