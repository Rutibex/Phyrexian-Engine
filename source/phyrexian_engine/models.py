
from dataclasses import dataclass, field
from typing import List, Dict, Optional

COLORS = ['W','U','B','R','G']
RARITIES = ['common','uncommon','rare','mythic']
CARD_TYPES = ['Creature','Instant','Sorcery','Enchantment','Artifact','Land']

RARITY_SLOTS = {
    'common': (1,1),
    'uncommon': (1,3),
    'rare': (2,4),
    'mythic': (3,4)
}

@dataclass
class SetSpec:
    name: str
    code: str
    description: str
    total_cards: int = 100
    colors: List[str] = field(default_factory=lambda: ['W','U','B','R','G'])
    include_artifacts: bool = True
    include_lands: bool = True
    rarity_weights: Dict[str, int] = field(default_factory=lambda: {'common': 60, 'uncommon': 25, 'rare': 12, 'mythic': 3})
    type_weights: Dict[str, int] = field(default_factory=lambda: {'Creature': 55, 'Instant': 10, 'Sorcery': 10, 'Enchantment': 10, 'Artifact': 10, 'Land': 5})
    seed: Optional[int] = None
    target_curve: Dict[int, float] = field(default_factory=dict)
    selected_packages: List[str] = field(default_factory=list)
    commander_mode: bool = False

@dataclass
class Card:
    temp_id: str
    color_identity: List[str]
    types: List[str]
    mana_value: int
    mana_cost: str
    rules_text: str
    rarity: str
    power: Optional[int] = None
    toughness: Optional[int] = None
    subtypes: List[str] = field(default_factory=list)
    name: Optional[str] = None
    art_description: Optional[str] = None
    flavor_text: Optional[str] = None

    def typeline(self) -> str:
        main = " ".join([t for t in self.types if t != '—'])
        sub = " ".join(dict.fromkeys(self.subtypes)).strip()  # de-dup subtypes
        return main if not sub else f"{main} — {sub}"

@dataclass
class CardSet:
    spec: SetSpec
    cards: List[Card] = field(default_factory=list)
