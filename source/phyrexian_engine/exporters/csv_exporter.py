
import csv, os
from ..models import CardSet

HEAD = ["Name","ManaCost","ManaValue","TypeLine","Rarity","Rules","P","T","Flavor","Art","Colors","Subtypes"]

def export_csv(card_set:CardSet, out_path:str)->str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(HEAD)
        for c in card_set.cards:
            w.writerow([c.name or "", c.mana_cost, c.mana_value, c.typeline(), c.rarity, c.rules_text.replace("\n"," / "),
                        c.power if c.power is not None else "", c.toughness if c.toughness is not None else "",
                        c.flavor_text or "", c.art_description or "", "".join(c.color_identity) or "C", " ".join(c.subtypes)])
    return out_path
