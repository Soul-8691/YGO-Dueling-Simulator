from .deck import Deck

class Player:
    def __init__(self, name, deck):
        self.name = name
        self.life_points = 8000
        self.hand = []
        self.field = []
        self.deck = deck

    def draw(self):
        card = self.deck.draw()   # must return a single Card object
        if card:
            self.hand.append(card)
        return card

    def to_dict(self):
        return {
            'name': self.name,
            'lp': self.life_points,
            'hand': [c.to_dict() for c in self.hand],   # hand must be Card objects
            'field': [c.to_dict() for c in self.field],
        }