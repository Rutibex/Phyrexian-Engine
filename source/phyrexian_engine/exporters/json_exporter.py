
import json, os
from ..models import CardSet

def export_json(card_set:CardSet, out_path:str)->str:
    data = {
        "set": {"name": card_set.spec.name, "code": card_set.spec.code, "description": card_set.spec.description, "total": len(card_set.cards)},
        "cards": [{
            "name": c.name, "mana_cost": c.mana_cost, "mana_value": c.mana_value, "types": c.types, "subtypes": c.subtypes,
            "rarity": c.rarity, "rules_text": c.rules_text, "power": c.power, "toughness": c.toughness,
            "flavor_text": c.flavor_text, "art_description": c.art_description, "color_identity": c.color_identity
        } for c in card_set.cards]
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path
