import uuid
from .player import Player
from .card import Card
from .deck import Deck

class GameState:
    def __init__(self):
        import uuid
        self.id = str(uuid.uuid4())
        self.players = {}   # key = socket_id, value = Player object
        self.turn = None    # current player's socket_id
        self.started = False

    def end_turn(self):
        if not self.started or not self.turn:
            return  # nothing to do
        # Get all player socket IDs
        player_ids = list(self.players.keys())
        # Switch to the other player
        self.turn = player_ids[1] if self.turn == player_ids[0] else player_ids[0]    

    def add_player(self, sid, name):
        from .deck import Deck
        from .card import Card
        from .player import Player

        # Sample cards for demonstration
        sample_cards = [Card("Blue-Eyes White Dragon", 3000, 2500),
                        Card("Dark Magician", 2500, 2100)] * 5

        if sid not in self.players:
            deck = Deck(sample_cards[:])
            player = Player(name, deck)
            # draw initial hand
            for _ in range(5):
                player.draw()
            self.players[sid] = player

        # Start the game when two players are present
        if len(self.players) == 2 and not self.started:
            self.turn = list(self.players.keys())[0]
            self.started = True

        return self.players[sid]
    

    def remove_player(self, sid):
        if sid in self.players:
            del self.players[sid]

            # If the player leaving was the one whose turn it was, switch turn
            if self.turn == sid:
                remaining_players = list(self.players.keys())
                self.turn = remaining_players[0] if remaining_players else None

            # If fewer than 2 players remain, mark game as not started
            if len(self.players) < 2:
                self.started = False

    def to_dict(self):
        return {
            'id': self.id,
            'started': self.started,
            'turn': self.turn,
            'players': {sid: player.to_dict() for sid, player in self.players.items()}
        }