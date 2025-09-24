from game.game import GameState
from game.card import Card
from game.deck import Deck
from game.player import Player

class YGOEngine:
    def __init__(self):
        self.games = {}  # key = game_id, value = GameState object

    # -------------------------
    # Game Management
    # -------------------------
    def create_game(self):
        game = GameState()
        self.games[game.id] = game
        return game.id

    def get_game(self, game_id):
        return self.games.get(game_id)

    def remove_game(self, game_id):
        if game_id in self.games:
            del self.games[game_id]

    # -------------------------
    # Player Management
    # -------------------------
    def add_player_to_game(self, game_id, sid, name):
        game = self.get_game(game_id)
        if game:
            return game.add_player(sid, name)
        return None

    def remove_player_from_game(self, game_id, sid):
        game = self.get_game(game_id)
        if game:
            game.remove_player(sid)
            if not game.players:
                self.remove_game(game_id)

    # -------------------------
    # Turn Management
    # -------------------------
    def end_turn(self, game_id):
        game = self.get_game(game_id)
        if game:
            game.end_turn()

    def get_current_turn(self, game_id):
        game = self.get_game(game_id)
        if game:
            return game.turn
        return None

    # -------------------------
    # Player Actions
    # -------------------------
    def draw_card(self, game_id, sid):
        game = self.get_game(game_id)
        if game and sid in game.players:
            card = game.players[sid].draw()
            return card.name if card else None
        return None

    def summon_card(self, game_id, sid, card_name):
        game = self.get_game(game_id)
        if game and sid in game.players:
            player = game.players[sid]
            for card in player.hand:
                if card.name == card_name:
                    player.hand.remove(card)
                    player.field.append(card)
                    return True
        return False

    def get_player_hand(self, game_id, sid):
        game = self.get_game(game_id)
        if game and sid in game.players:
            return [card.name for card in game.players[sid].hand]
        return []

    def get_player_field(self, game_id, sid):
        game = self.get_game(game_id)
        if game and sid in game.players:
            return [card.name for card in game.players[sid].field]
        return []
    
    def play_card(self, game_id, sid, card_name):
        """Play a card from hand to field."""
        return self.summon_card(game_id, sid, card_name)

    # -------------------------
    # Game State
    # -------------------------
    def game_state(self, game_id):
        game = self.get_game(game_id)
        if game:
            return game.to_dict()
        return {}