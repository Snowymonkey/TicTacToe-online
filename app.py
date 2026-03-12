from flask import Flask, render_template, request, redirect, session, abort, url_for
import secrets
import threading
import time
app = Flask(__name__)
app.secret_key = "" # CHANGE TO OWN SECRET KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False 
)

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
        "winner":-1,
        "created": time.time()
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
    clean_up()

    game_id = secrets.token_urlsafe(6)
    with games_lock:
        games[game_id] = initGame()
    return redirect(url_for('game', game_id=game_id))

@app.route("/game/<game_id>")
def game(game_id):
    clean_up()

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

    clean_up()

    if game_id not in games:
        abort(404)

    with games_lock:
        game = games[game_id]

        token = session.get(f"player_{game_id}")
        if token and token in game["players"]:
            return redirect(url_for('game', game_id=game_id))

        if len(game["players"]) >= 2:
            return "Game is full :(", 400

        token = secrets.token_urlsafe(8)
        game["players"].append(token)
        session[f"player_{game_id}"] = token

    return redirect(url_for('game', game_id=game_id))
        


@app.route("/move/<game_id>", methods=["POST"])
def move(game_id):
    
    clean_up()

    if game_id not in games:
        abort(404)

    row = int(request.form["row"])
    column = int(request.form["column"])
    
    token = session.get(f"player_{game_id}")
    if not token:
        return "You are not the player in this game. Join first", 403
    
    if (row > 3 or row < 0) or (column > 3 or column < 0):
        abort(400)

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

def clean_up():
    now = time.time()
    expired = []
    for game_id, game in games.items():
        if now - game["created"] > 3600:
            expired.append(game_id)
    for game_id in expired:
        del games[game_id]

print(secrets.token_hex(32))
app.run(debug=False)
