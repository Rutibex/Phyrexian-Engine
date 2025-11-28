import random
from typing import List
from ..models import SetSpec

# Default mana curve weights (favoring 2–4 MV)
DEFAULT_CURVE = {1: 10, 2: 18, 3: 20, 4: 16, 5: 10, 6: 6}

def sample_mana_value(curve:dict)->int:
    vals = []
    for mv, w in curve.items():
        vals += [mv]*w
    return random.choice(vals)

def rarity_bucket(spec:SetSpec)->str:
    # Weighted rarities
    weights = {'Common': 100, 'Uncommon': 35, 'Rare': 15, 'Mythic': 5}
    pool = []
    for k, w in weights.items():
        pool += [k]*w
    return random.choice(pool)

def plan_types(spec:SetSpec)->List[str]:
    """Returns a planned list of card types matching set size and toggles.
    Added new supported pseudo-types:
      - AuraCreature
      - AuraLand
      - Equipment
    These behave as Enchantments/Artifacts but get generated distinctly."""
    # Commander Mode: only creatures (these will become Legendary in cardgen)
    if getattr(spec, "commander_mode", False):
        total = max(1, spec.total_cards)
        return ["Creature"] * total    
    base_types = ['Creature','Instant','Sorcery','Enchantment','Artifact']
    if spec.include_lands:
        base_types.append('Land')
    # Add the new subtypes with smaller weights
    extended_types = base_types + ['AuraCreature','AuraLand','Equipment']

    weights = {
        'Creature': 45,
        'Instant': 15,
        'Sorcery': 15,
        'Enchantment': 10,
        'Artifact': 8,
        'Land': 5,
        'AuraCreature': 6,
        'AuraLand': 4,
        'Equipment': 6,
    }
    pool = []
    for t, w in weights.items():
        pool += [t]*w
    random.shuffle(pool)
    total = max(1, spec.total_cards)
    chosen = [random.choice(pool) for _ in range(total)]
    return chosen
