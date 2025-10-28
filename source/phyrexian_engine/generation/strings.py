# generation/strings.py
import random, re

# Tokens we should never replace (MTG symbols etc.)
SKIP_TOKENS = {"T", "W", "U", "B", "R", "G"}

# Sensible defaults if a pool is missing
DEFAULT_POOLS = {
    "TRIGGER_INTRO": ["When", "Whenever"],
    "CREATURE_CONTROLLER": ["you control", "an opponent controls"],
    "CREATURE_TRIGGER": ["enters the battlefield", "dies", "attacks", "blocks"],
    "TOKEN_COLOR": ["{C}"],  # will be converted to a color word in the numeric/color pass
    "ACTIVATED_COST": ["{2}:"],
    "ACTIVATED_EFFECT": ["Draw a card."],
    "EQUIP_COST": ["{2}"],
    # Some other common buckets your packages may use:
    "PERMANENT_CONTROLLER": ["you control", "an opponent controls"],
    "TARGET_OPPONENT": ["target opponent"],
}

def _pick_color_word(colors):
    if not colors:
        return "colorless"
    for sym, word in [("W","white"),("U","blue"),("B","black"),("R","red"),("G","green")]:
        if sym in colors:
            return word
    return "colorless"

def _pick_token_subtype(colors, string_pools, subtypes_pool):
    merged = []
    merged += string_pools.get("TOKEN_SUBTYPE", [])
    for c in colors or []:
        merged += subtypes_pool.get(c, [])
    if not merged:
        merged = ["Soldier", "Spirit", "Zombie", "Wolf"]
    return random.choice(merged)

def _sub_token_any(text: str, token: str, value: str) -> str:
    """
    Replace either {TOKEN} or [TOKEN] with value (case-insensitive).
    """
    pattern = re.compile(rf"(\{{{token}\}}|\[{token}\])", re.IGNORECASE)
    return pattern.sub(value, text)

def _find_all_tokens(text: str):
    """
    Return a set of raw token names found inside {...} or [...] (without braces/brackets).
    Case-insensitive: returned in UPPERCASE.
    """
    tokens = set()
    for m in re.finditer(r"\{([A-Za-z0-9_/]+)\}|\[([A-Za-z0-9_/]+)\]", text):
        tok = m.group(1) or m.group(2)
        if tok:
            tokens.add(tok.upper())
    return tokens

def _fill_categories_generic(text, colors, string_pools, subtypes_pool):
    """
    Generic pass: replace any tokens that have a pool (string_pools or DEFAULT_POOLS),
    plus special handling for TOKEN_SUBTYPE and TOKEN_COLOR.
    """
    tokens = _find_all_tokens(text)

    for tok in tokens:
        if tok in SKIP_TOKENS:
            continue
        # Skip numeric/color handled later
        if tok in {"N", "X", "X/X", "C"}:
            continue

        value = None

        if tok == "TOKEN_SUBTYPE":
            value = _pick_token_subtype(colors, string_pools, subtypes_pool)
        elif tok in {"TOKEN_COLOR", "COLOR_WORD"}:
            # Put a placeholder that the numeric/color pass will convert
            # to a language color word; if a pool exists, we can sample it first
            pool = string_pools.get(tok, DEFAULT_POOLS.get(tok, []))
            if pool:
                value = random.choice(pool)
            else:
                value = "{C}"
        else:
            # Any other token: look up in user pools or default pools
            pool = string_pools.get(tok, None)
            if not pool or not isinstance(pool, list) or not pool:
                pool = DEFAULT_POOLS.get(tok, None)
            if pool:
                value = random.choice(pool)

        if value is not None:
            text = _sub_token_any(text, tok, value)

    return text

def _finalize_numbers_and_colors(text, colors, mv):
    # {N} or [N]
    n = max(1, min(5, mv))
    text = _sub_token_any(text, "N", str(n))

    # {X}/{X} or [X]/[X] first
    xval = max(1, min(6, mv))
    pattern_xx = re.compile(r"(\{X\}|\[X\])\s*/\s*(\{X\}|\[X\])", re.IGNORECASE)
    text = pattern_xx.sub(f"{xval}/{xval}", text)
    # then any single X
    text = re.sub(r"(\{X\}|\[X\])", str(xval), text, flags=re.IGNORECASE)

    # {C} or [C] -> color word (white/blue/...)
    color_word = _pick_color_word(colors)
    text = _sub_token_any(text, "C", color_word)

    return text

def finalize_effect_template(template, colors, mv, string_pools, subtypes_pool):
    # First, a generic fill for any token present in pools or defaults
    step1 = _fill_categories_generic(template, colors, string_pools, subtypes_pool)
    # Then do numbers and color conversions
    step2 = _finalize_numbers_and_colors(step1, colors, mv)
    # Normalize whitespace PER LINE, but keep intended line breaks
    import re as _re
    lines = [_re.sub(r"\s+", " ", ln).strip() for ln in step2.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
