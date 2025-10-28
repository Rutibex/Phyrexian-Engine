
import os, io, zipfile
from datetime import datetime
from ..models import CardSet

HEADER_TEMPLATE = (
    "mse version: 0.3.8\n"
    "game: magic\n"
    "stylesheet: m15\n"
    "set info:\n"
    "\tcode: {code}\n"
    "\tname: {name}\n"
    "\trarity scheme: magic rarity\n"
    "\tdefault language: English\n"
)

def _esc(v:str)->str:
    if v is None: return ""
    return str(v).replace("\r\n","\n").replace("\r","\n")

def _render_card(card, idx:int, now_str:str)->str:
    name = _esc(card.name or "Unnamed")
    cost = _esc(card.mana_cost or "")
    rarity = _esc(card.rarity or "")
    rules = _esc(card.rules_text or "")
    flavor = _esc(card.flavor_text or "")
    type_line = _esc(card.typeline())

    out = []
    out.append("card:")
    out.append("\thas_styling: false")
    out.append("\tnotes: ")
    out.append(f"\ttime_created: {now_str}")
    out.append(f"\ttime_modified: {now_str}")
    out.append(f"\tname: {name}")
    if cost:
        out.append(f"\tcasting_cost: {cost}")
    out.append(f"\tsuper_type: <word-list-type-en>{type_line}</word-list-type-en>")
    out.append("\tsuper_type_2: <word-list-type-en></word-list-type-en>")
    out.append("\tsuper_type_3: <word-list-type-en></word-list-type-en>")
    out.append("\tsuper_type_4: <word-list-type-en></word-list-type-en>")
    # leave sub_type empty to avoid duplication
    out.append("\tsub_type: <word-list-race-en></word-list-race-en>")
    out.append("\tsub_type_2: ")
    out.append("\tsub_type_3: ")
    out.append("\tsub_type_4: ")
    if rarity:
        out.append(f"\trarity: {rarity}")
    out.append("\trule_text:")
    if rules:
        for ln in rules.split("\n"):
            out.append(f"\t\t{ln}")
    if flavor.strip():
        out.append(f"\tflavor_text: <i-flavor>{flavor}</i-flavor>")
    else:
        out.append("\tflavor_text: <i-flavor></i-flavor>")
    if card.power is not None and card.toughness is not None:
        out.append(f"\tpower: {card.power}")
        out.append(f"\ttoughness: {card.toughness}")
    out.append("\timage: ")
    out.append("\timage_2: ")
    out.append("\tmainframe_image: ")
    out.append("\tmainframe_image_2: ")
    out.append("\tcard_code_text: ")
    out.append("\tcard_code_text_2: ")
    out.append("\tcard_code_text_3: ")
    return "\n".join(out) + "\n"

def export_mse(card_set:CardSet, out_path:str)->str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = HEADER_TEMPLATE.format(code=_esc(card_set.spec.code), name=_esc(card_set.spec.name))
    parts = [header]
    for i,c in enumerate(card_set.cards, start=1):
        parts.append(_render_card(c, i, now_str))
    set_text = "\n".join(parts)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("set", set_text.encode("utf-8"))
    with open(out_path, "wb") as f:
        f.write(mem.getvalue())
    return out_path
