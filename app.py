from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from ygo_engine import YGOEngine  # your engine class

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
socketio = SocketIO(app, cors_allowed_origins='*')

# initialize the YGO engine
engine = YGOEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<game_id>')
def game_page(game_id):
    return render_template('board.html', game_id=game_id)

@app.route('/create')
def create_game():
    # create a new game and get its ID
    game_id = engine.create_game()
    return redirect(url_for('game_page', game_id=game_id))

# -------------------------
# Socket handlers
# -------------------------

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id')
    name = data.get('name', 'Player')
    sid = request.sid

    if not engine.game_state(game_id):
        emit('error', {'error': 'game not found'})
        return

    player = engine.add_player_to_game(game_id, sid, name)
    join_room(game_id)
    emit('game_state', engine.game_state(game_id), room=game_id)

@socketio.on('play_card')
def handle_play_card(data):
    game_id = data.get('game_id')
    card_id = data.get('card_id')

    if not engine.game_state(game_id):
        emit('error', {'error': 'game not found'})
        return

    engine.play_card(game_id, request.sid, card_id)
    emit('game_state', engine.game_state(game_id), room=game_id)

@socketio.on('attack')
def handle_attack(data):
    game_id = data.get('game_id')
    attacker_card_id = data.get('attacker_card_id')
    target_card_id = data.get('target_card_id')

    if not engine.game_state(game_id):
        emit('error', {'error': 'game not found'})
        return

    engine.attack(game_id, request.sid, attacker_card_id, target_card_id)
    emit('game_state', engine.game_state(game_id), room=game_id)

@socketio.on('end_turn')
def handle_end_turn(data):
    game_id = data.get('game_id')

    if not engine.game_state(game_id):
        emit('error', {'error': 'game not found'})
        return

    sid = request.sid
    if sid != engine.game_state(game_id)['turn']:
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