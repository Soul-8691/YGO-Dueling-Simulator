from game.game import GameState
from game.card import Card
from game.deck import Deck
from game.player import Player
import json

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

    def add_player_to_game(self, game_id, sid, name, deck_data):
        # Convert deck_data to dict if it's a string
        if isinstance(deck_data, str):
            try:
                deck_data = json.loads(deck_data)
            except json.JSONDecodeError:
                deck_data = {"main": [], "extra": []}  # fallback if invalid JSON

        game = self.games.get(game_id)
        if not game:
            return None  # or raise error

        player = game.add_player(sid, name, deck_data)
        return player

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
        game = self.get_game(game_id)
        if game and sid in game.players:
            player = game.players[sid]
            for card in player.hand:
                if card.name == card_name:
                    player.hand.remove(card)
                    player.field.append(card)  # ✅ append actual Card object
                    return True
        return False

    # -------------------------
    # Game State
    # -------------------------
    def game_state(self, game_id):
        game = self.get_game(game_id)
        if game:
            return game.to_dict()
        return {}