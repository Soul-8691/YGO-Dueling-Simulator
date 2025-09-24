from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Card:
    id: str
    name: str
    attack: int = 0
    defense: int = 0
    image: Optional[str] = None

    def to_dict(self):
        return asdict(self)