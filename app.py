from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from ygo_engine import YGOEngine  # your engine class
import os
import json
from werkzeug.utils import secure_filename
from urllib.parse import unquote

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
socketio = SocketIO(app, cors_allowed_origins='*')
#initialize the decks
# Load your GOAT format cards JSON
with open("goat_format_cards_local.json", "r", encoding="utf-8") as f:
    GOAT_CARDS = json.load(f)

app.config['GOAT_CARDS'] = {c['name']: c for c in GOAT_CARDS}

# User deck storage
USER_DECKS_DIR = "user_decks"
os.makedirs(USER_DECKS_DIR, exist_ok=True)

def save_user_deck(username, deck_name, cards):
    user_folder = os.path.join(USER_DECKS_DIR, username)
    os.makedirs(user_folder, exist_ok=True)
    path = os.path.join(user_folder, f"{deck_name}.ydk")
    with open(path, "w", encoding="utf-8") as f:
        f.write("#created by Flask DeckBuilder\n")
        f.write("#main\n")
        for card in cards.get("main", []):
            f.write(f"{card}\n")
        f.write("#extra\n")
        for card in cards.get("extra", []):
            f.write(f"{card}\n")
        f.write("!side\n")
        for card in cards.get("side", []):
            f.write(f"{card}\n")
    return path

def load_user_decks(username):
    user_folder = os.path.join(USER_DECKS_DIR, username)
    decks = {}
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            if file.endswith(".ydk"):
                decks[file] = os.path.join(user_folder, file)
    return decks


@app.route("/load_ydk/<path:deck_file>")
def load_ydk(deck_file):
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    username = session["username"]
    deck_file = unquote(deck_file)  # decode URL-encoded deck names
    user_folder = os.path.join(USER_DECKS_DIR, username)

    # Check if user folder exists
    if not os.path.exists(user_folder):
        return jsonify({"error": "User folder not found"}), 404

    path = os.path.join(user_folder, deck_file)

    # Check if deck file exists
    if not os.path.exists(path):
        return jsonify({"error": "Deck not found"}), 404

    main, extra, side = [], [], []
    current_section = None

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#created"):
                    continue
                if line == "#main":
                    current_section = main
                elif line == "#extra":
                    current_section = extra
                elif line == "!side":
                    current_section = side
                elif current_section is not None:
                    current_section.append(line)
    except Exception as e:
        return jsonify({"error": f"Failed to read deck: {str(e)}"}), 500

    return jsonify({"main": main, "extra": extra, "side": side})

# -----------------------
# Login / User Session
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        if username:
            session["username"] = secure_filename(username)
            os.makedirs(os.path.join(USER_DECKS_DIR, username), exist_ok=True)
            return redirect(url_for("deckbuilder"))
    return render_template("login.html")

# -----------------------
# Deckbuilder
# -----------------------
@app.route("/deckbuilder", methods=["GET", "POST"])
def deckbuilder():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    user_dir = os.path.join(USER_DECKS_DIR, username)

    if request.method == "POST":
        data = request.json
        main = data.get("main", [])
        extra = data.get("extra", [])
        side = data.get("side", [])
        deck_name = data.get("deck_name", "mydeck")
        
        # GOAT validation
        if len(main) > 40 or len(extra) > 15 or len(side) > 15:
            return {"error": "Deck exceeds GOAT limits!"}, 400

        # Save as .ydk
        ydk_path = os.path.join(user_dir, f"{secure_filename(deck_name)}.ydk")
        with open(ydk_path, "w", encoding="utf-8") as f:
            # YDK format: #main, #extra, #side
            f.write("#main\n" + "\n".join(main) + "\n")
            f.write("#extra\n" + "\n".join(extra) + "\n")
            f.write("!side\n" + "\n".join(side) + "\n")
        
        return {"success": True, "deck_name": deck_name}

    # GET request: show builder
    user_decks = [f for f in os.listdir(user_dir) if f.endswith(".ydk")]
    return render_template("deckbuilder.html", goat_cards=GOAT_CARDS, user_decks=user_decks)

# -----------------------
# Download deck
# -----------------------
@app.route("/download/<deck_name>")
def download(deck_name):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    path = os.path.join(USER_DECKS_DIR, username, secure_filename(deck_name) + ".ydk")
    if not os.path.exists(path):
        return "Deck not found!", 404
    return send_file(path, as_attachment=True)

# initialize the YGO engine
engine = YGOEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<game_id>')
def game_page(game_id):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    user_decks = [f for f in os.listdir(os.path.join(USER_DECKS_DIR, username)) if f.endswith(".ydk")]
    return render_template('board.html', game_id=game_id, user_decks=user_decks)

@app.route('/create')
def create_game():
    game_id = engine.create_game()
    return redirect(url_for('game_page', game_id=game_id))

# -------------------------
# Socket handlers
# -------------------------

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id')
    sid = request.sid
    username = session.get("username")
    deck = data.get("deck", {})

    if not username:
        emit('error', {'error': 'User not logged in'}, room=sid)
        return

    engine.add_player_to_game(game_id, sid, username, deck)
    join_room(game_id)

    # emit updated game state to everyone in the room
    emit('game_state', engine.game_state(game_id), room=game_id)

@socketio.on('play_card')
def handle_play_card(data):
    game_id = data.get('game_id')
    card_id = data.get('card_id')
    sid = request.sid

    game = engine.game_state(game_id)
    if not game:
        emit('error', {'error': 'game not found'}, room=sid)
        return

    if sid not in game['players']:
        emit('error', {'error': 'Not in this game!'}, room=sid)
        return

    engine.play_card(game_id, sid, card_id)
    emit('game_state', engine.game_state(game_id), room=game_id)


@socketio.on('attack')
def handle_attack(data):
    game_id = data.get('game_id')
    attacker_card_id = data.get('attacker_card_id')
    target_card_id = data.get('target_card_id')
    sid = request.sid

    game = engine.game_state(game_id)
    if not game:
        emit('error', {'error': 'game not found'}, room=sid)
        return

    if sid not in game['players']:
        emit('error', {'error': 'Not in this game!'}, room=sid)
        return

    engine.attack(game_id, sid, attacker_card_id, target_card_id)
    emit('game_state', engine.game_state(game_id), room=game_id)


@socketio.on('end_turn')
def handle_end_turn(data):
    game_id = data.get('game_id')
    sid = request.sid

    game = engine.game_state(game_id)
    if not game:
        emit('error', {'error': 'game not found'}, room=sid)
        return

    if sid != game['turn']:
        emit('error', {'error': "It's not your turn!"}, room=sid)
        return

    engine.end_turn(game_id)
    emit('game_state', engine.game_state(game_id), room=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    # remove player from any games they were in
    for game_id in list(engine.games.keys()):
        engine.remove_player_from_game(game_id, sid)
        socketio.emit('game_state', engine.game_state(game_id), room=game_id)