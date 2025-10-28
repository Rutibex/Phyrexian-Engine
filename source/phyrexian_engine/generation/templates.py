# generation/templates.py
import json, os, random
from typing import Dict, List, Tuple, Any, Optional

# Effects store type
# effects_by_color[color][type] = List[ (template:str, weight:int, min_mv:int, max_mv:int) ]
EffectsByColor = Dict[str, Dict[str, List[Tuple[str, int, int, int]]]]

def _merge_effects(dst: EffectsByColor, src: EffectsByColor) -> None:
    for color, by_type in src.items():
        dst.setdefault(color, {})
        for typ, entries in by_type.items():
            dst[color].setdefault(typ, [])
            # trust entries format [tmpl, weight, min, max]
            for e in entries:
                if isinstance(e, (list, tuple)) and len(e) >= 4:
                    tmpl, w, mn, mx = e[0], int(e[1]), int(e[2]), int(e[3])
                    dst[color][typ].append((tmpl, w, mn, mx))

def _merge_lists(dst: Dict[str, List[str]], src: Dict[str, List[str]]) -> None:
    for k, vals in src.items():
        if not isinstance(vals, list): 
            continue
        dst.setdefault(k, [])
        # extend + dedupe
        seen = set(dst[k])
        for v in vals:
            if v not in seen:
                dst[k].append(v)
                seen.add(v)

def _merge_keywords(dst: Dict[str, List[str]], src: Dict[str, List[str]]) -> None:
    for color, vals in src.items():
        if not isinstance(vals, list):
            continue
        dst.setdefault(color, [])
        seen = set(dst[color])
        for v in vals:
            if v not in seen:
                dst[color].append(v)
                seen.add(v)

def load_packages(pack_dir: str, selected: List[str]):
    """
    Returns: (effects_by_color, creature_subtypes, string_pools, monster_keywords)
    - effects_by_color[color][type] = [(template, weight, min_mv, max_mv), ...]
    - creature_subtypes[color] = [subtype, ...]
    - string_pools[TOKEN] = [variants...]
    - monster_keywords[color] = [kw...]
    """
    effects: EffectsByColor = {}
    subtypes_pool: Dict[str, List[str]] = {}
    string_pools: Dict[str, List[str]] = {}
    monster_keywords: Dict[str, List[str]] = {}

    for base in selected:
        path = os.path.join(pack_dir, base if base.endswith(".json") else base + ".json")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # effects_by_color
        eff_raw = data.get("effects_by_color", {})
        eff_norm: EffectsByColor = {}
        for color, by_type in eff_raw.items():
            eff_norm.setdefault(color, {})
            for typ, entries in by_type.items():
                eff_norm[color].setdefault(typ, [])
                for e in entries or []:
                    if isinstance(e, (list, tuple)) and len(e) >= 4:
                        tmpl, w, mn, mx = e[0], int(e[1]), int(e[2]), int(e[3])
                        eff_norm[color][typ].append((tmpl, w, mn, mx))
        _merge_effects(effects, eff_norm)

        # creature_subtypes
        subs = data.get("creature_subtypes", {})
        _merge_lists(subtypes_pool, subs)

        # string_pools
        pools = data.get("string_pools", {})
        # normalize keys to UPPER so templates may reference tokens case-insensitively
        pools_upper = {k.upper(): v for (k, v) in pools.items() if isinstance(v, list)}
        _merge_lists(string_pools, pools_upper)

        # monster_keywords
        kws = data.get("monster_keywords", {})
        _merge_keywords(monster_keywords, kws)

    return effects, subtypes_pool, string_pools, monster_keywords

def _weighted_choice(candidates: List[Tuple[str, int, int, int]]) -> Optional[str]:
    # candidates: list of (template, weight, min_mv, max_mv)
    total = sum(max(0, w) for _, w, _, _ in candidates)
    if total <= 0:
        # uniform if all weights are zero/negative
        return random.choice(candidates)[0] if candidates else None
    r = random.randint(1, total)
    acc = 0
    for tmpl, w, _, _ in candidates:
        acc += max(0, w)
        if r <= acc:
            return tmpl
    return candidates[-1][0] if candidates else None

def pick_effect(effects_by_color: EffectsByColor,
                string_pools,  # kept for signature compatibility; not used here
                subtypes_pool, # kept for signature compatibility; not used here
                type_key: str,
                colors: List[str],
                mv: int) -> str:
    """
    Choose one template for the given (type_key, colors, mv) with:
      - search order: each color in colors -> 'any' -> 'C'
      - inclusive min/max mv filter
      - weighted random by 'weight'
    Returns "" if nothing applicable.
    """
    # Build search order
    order: List[str] = []
    # card colors (in order provided)
    for c in colors or []:
        if c not in order:
            order.append(c)
    # then generic pools
    for fallback in ("any", "C"):
        if fallback not in order:
            order.append(fallback)

    # Collect all candidates from color buckets
    candidates: List[Tuple[str, int, int, int]] = []
    for col in order:
        by_type = effects_by_color.get(col, {})
        for tmpl, w, mn, mx in by_type.get(type_key, []):
            if mn <= mv <= mx:
                candidates.append((tmpl, w, mn, mx))

    if not candidates:
        return ""

    tmpl = _weighted_choice(candidates)
    return tmpl or ""
