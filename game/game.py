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

    def add_player(self, sid, name, deck_data=None):
        from .deck import Deck
        from .card import Card
        from .player import Player
        from flask import current_app

        if sid not in self.players:
            cards = []
            if deck_data:  # user deck from JS
                for cname in deck_data.get("main", []):
                    card_info = current_app.config['GOAT_CARDS'].get(cname)
                    if card_info:
                        cards.append(Card(
                            name=card_info['name'],
                            attack=int(card_info.get('atk') or 0),
                            defense=int(card_info.get('def') or 0),
                            card_type=card_info.get('type', 'Monster'),
                            attribute=card_info.get('attribute'),
                            level=card_info.get('level'),
                            effect=card_info.get('desc', ''),
                            image=card_info.get('local_images', '/static/images/default_card.png')
                        ))
           

            deck = Deck(cards)
            player = Player(name, deck)

            # Draw initial hand (actual Card objects)
            for _ in range(5):
                player.draw()

            self.players[sid] = player

        # Start game when 2 players present
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