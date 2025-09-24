import random
from .card import Card

class Deck:
    def __init__(self, cards):
        self.cards = cards  # list of Card objects
        import random
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None