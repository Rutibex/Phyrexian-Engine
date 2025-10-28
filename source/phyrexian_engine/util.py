import re


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def make_mana_cost(mv:int, colors:list)->str:
    """Return a mana cost string based on the card's mana value (mv) and color identity.

    This version enforces:
    - Multicolored cards may get hybrid or Phyrexian style pips.
    - Otherwise we fall back to normal generic+colored pips.
    NOTE:
    Lands will have their cost cleared in cardgen.generate_card(), so we still
    return "0" here for mv==0 to keep artifacts with true 0 cost valid.
    """
    import random

    order = ['W','U','B','R','G']
    # normalize/ordering for deterministic symbol order (WUBRG)
    cols = [c for c in order if c in (colors or [])]

    # No cost case
    if mv <= 0:
        return "0"

    # Multicolor special handling (2+ colors)
    if len(cols) >= 2:
        c1, c2 = cols[0], cols[1]
        style_pick = random.random()
        # try ~1/3 hybrid, ~1/3 phyrexian, ~1/3 normal multicolor
        if style_pick < 1/3:
            # Hybrid style: generic then two identical hybrid pips like (W/U)(W/U)
            generic = max(mv - 2, 0)
            parts = []
            if generic > 0:
                parts.append(str(generic))
            parts.append(f"({c1}/{c2})")
            parts.append(f"({c1}/{c2})")
            return "".join(parts)
        elif style_pick < 2/3:
            # Phyrexian style: generic then one phyrexian pip (W/P) plus the other color
            generic = max(mv - 2, 0)
            parts = []
            if generic > 0:
                parts.append(str(generic))
            parts.append(f"({c1}/P)")
            parts.append(c2)
            return "".join(parts)
        # else fall through to normal below

    # Normal mono / multicolor cost:
    # number of colored pips is min(#colors, mv)
    colored = min(len(cols), mv)
    generic = mv - colored
    pips = []
    if generic > 0:
        pips.append(str(generic))
    # add colored pips in WUBRG order
    count = 0
    for c in order:
        if c in cols and count < colored:
            pips.append(c)
            count += 1
    return "".join(pips)


def sanitize_filename(name:str)->str:
    return re.sub(r'[^A-Za-z0-9_\-]+', '_', name)[:64]
