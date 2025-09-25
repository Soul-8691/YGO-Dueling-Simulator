from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Card:
    def __init__(self, name, attack=0, defense=0, card_type="Monster", attribute=None, level=None, effect="", image=None):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.card_type = card_type
        self.attribute = attribute
        self.level = level
        self.effect = effect
        self.image = image  # ✅ add this

    def to_dict(self):
        return {
            "name": self.name,
            "attack": self.attack,
            "defense": self.defense,
            "card_type": self.card_type,
            "attribute": self.attribute,
            "level": self.level,
            "effect": self.effect,
            "image": self.image
        }