import random
from typing import List
from .distribution import sample_mana_value, DEFAULT_CURVE, rarity_bucket
from ..models import Card, SetSpec, RARITY_SLOTS
from ..util import make_mana_cost
from .templates import pick_effect
from .strings import finalize_effect_template

# Default evergreen keywords by color; packages can add more via 'monster_keywords'
CREATURE_KEYWORDS_BY_COLOR = {
    'W': ['vigilance', 'lifelink', 'first strike'],
    'U': ['flying', 'ward {X}', 'flash'],
    'B': ['deathtouch', 'menace', 'lifelink'],
    'R': ['haste', 'first strike', 'menace'],
    'G': ['trample', 'reach', 'hexproof'],
}

# Fallbacks so we never emit blank rules text
DEFAULT_ENCHANTMENT_EFFECTS = [
    "Creatures you control get +{N}/+0.",
    "At the beginning of your upkeep, you gain {N} life.",
    "Whenever you cast a {C} spell, scry 1.",
    "Whenever a creature you control attacks, it gets +1/+0 until end of turn.",
]
DEFAULT_AURA_CREATURE = "Enchanted creature gets +{N}/+{N}."
DEFAULT_AURA_LAND = "Enchanted land has \"{T}: Add one mana of any color.\""
DEFAULT_EQUIPMENT = "Equipped creature gets +{N}/+{N}."

def _fallback_spell_effect(card_type: str, colors: List[str], mv: int) -> str:
    if card_type == 'Instant':
        boost = max(1, mv // 2)
        return f"Target creature gets +{boost}/+{boost} until end of turn."
    if card_type == 'Sorcery':
        count = max(1, mv)
        return f"Create {count} 1/1 {(' '.join(colors) + ' ' if colors else '')}creature token(s)."
    return "Draw a card."

def _slots_for_rarity(rarity: str) -> int:
    key = (rarity or '').lower()
    lo, hi = RARITY_SLOTS.get(key, (1, 1))
    return random.randint(lo, hi)

def _append_unique_effects(rules_parts, *, type_key: str, slots: int, colors: List[str], mv: int,
                           effects, string_pools, subtypes_pool, fallback_text: str = None,
                           attempts_per_slot: int = 6):
    """Pick up to `slots` effect lines without duplicates (post-finalization)."""
    from .strings import finalize_effect_template
    seen = set()
    added = 0
    for _ in range(max(0, slots)):
        chosen_raw = None
        for _try in range(max(1, attempts_per_slot)):
            eff = pick_effect(effects, string_pools, subtypes_pool, type_key, colors, mv)
            if not eff and fallback_text:
                eff = fallback_text
            if not eff:
                continue
            canon = finalize_effect_template(eff, colors, mv, string_pools, subtypes_pool).strip().lower()
            if canon and canon not in seen:
                chosen_raw = eff
                seen.add(canon)
                break
        if chosen_raw:
            rules_parts.append(chosen_raw)
            added += 1
    if added == 0 and fallback_text:
        rules_parts.append(fallback_text)
    return added


def _maybe_keywords(colors: List[str], mv: int, monster_keywords) -> List[str]:
    pool = []
    for c in colors or []:
        pool += CREATURE_KEYWORDS_BY_COLOR.get(c, [])
        if monster_keywords:
            pool += monster_keywords.get(c, [])
    k = 0
    r = random.random()
    if r < 0.25: k = 1
    elif r < 0.35: k = 2
    choices = []
    random.shuffle(pool)
    for kw in pool:
        if kw not in choices:
            x = max(1, min(6, mv))
            choices.append(kw.replace("{X}", str(x)))
        if len(choices) >= k:
            break
    return choices

def generate_card(code: str,
                  colors: List[str],
                  card_type: str,
                  spec: SetSpec,
                  effects,
                  subtypes_pool,
                  string_pools,
                  monster_keywords):
    # pick mana value up front
    mv = sample_mana_value(DEFAULT_CURVE)
    rarity = rarity_bucket(spec)

    # Lands should have no mana cost and mana value 0
    if card_type == 'Land':
        mv = 0

    color_id = "".join(colors) or None
    mana_cost = make_mana_cost(mv, colors)

    card = Card(
        temp_id=code,
        color_identity=color_id,
        mana_value=mv,
        mana_cost=mana_cost,
        rules_text="",
        rarity=rarity,
        types=[],
    )

    rules_parts: List[str] = []

    if card_type == 'Creature':
        # Commander mode: Legendary Creature
        if getattr(spec, "commander_mode", False):
            card.types = ['Legendary', 'Creature']
        else:
            card.types = ['Creature']

        base = max(1, mv - 1)
        card.power = base
        card.toughness = base + 1

        # Subtypes
        card.subtypes = []

        if getattr(spec, "commander_mode", False):
            # Build a pool from the commander’s colors + 'any'
            candidates = []
            for ccol in (colors or []):
                candidates.extend(subtypes_pool.get(ccol, []))
            candidates.extend(subtypes_pool.get('any', []))

            # Remove duplicates, randomize
            candidates = list(dict.fromkeys(candidates))
            random.shuffle(candidates)

            if candidates:
                max_types = 4
                min_types = 1
                n_types = random.randint(min_types, min(max_types, len(candidates)))
                card.subtypes = candidates[:n_types]
        else:
            # Existing behavior for non-commander sets
            for ccol in colors or []:
                if subtypes_pool.get(ccol):
                    card.subtypes.append(random.choice(subtypes_pool[ccol]))


        # Keyword abilities (first line, comma-separated)
        kw = _maybe_keywords(colors, mv, monster_keywords)
        if kw:
            seen_kw = set()
            kw = [k for k in kw if not (k in seen_kw or seen_kw.add(k))]
            if kw:
                kw_line = ", ".join(kw)
                rules_parts.append(kw_line[:1].upper() + kw_line[1:])

        # Ability lines scaled by rarity (one per line), deduped
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key="Creature",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text="When this creature enters the battlefield, {ACTIVATED_EFFECT}",
        )

    elif card_type in ('Instant', 'Sorcery'):
        card.types = [card_type]
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key=card_type,
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text=_fallback_spell_effect(card_type, colors, mv),
        )

    elif card_type == 'Enchantment':
        card.types = ['Enchantment']
        slots = max(1, _slots_for_rarity(rarity))
        _append_unique_effects(
            rules_parts,
            type_key="Enchantment",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text=random.choice(DEFAULT_ENCHANTMENT_EFFECTS),
        )

    elif card_type == 'Artifact':
        card.types = ['Artifact']
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key="Artifact",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text="{T}: Add one mana of any color.",
        )

    elif card_type == 'AuraCreature':
        card.types = ['Enchantment']; card.subtypes = ['Aura']
        rules_parts.append("Enchant creature")
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key="AuraCreature",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text=DEFAULT_AURA_CREATURE,
        )

    elif card_type == 'AuraLand':
        card.types = ['Enchantment']; card.subtypes = ['Aura']
        rules_parts.append("Enchant land")
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key="AuraLand",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text=DEFAULT_AURA_LAND,
        )

    elif card_type == 'Equipment':
        card.types = ['Artifact']; card.subtypes = ['Equipment']
        slots = _slots_for_rarity(rarity)
        _append_unique_effects(
            rules_parts,
            type_key="Equipment",
            slots=slots,
            colors=colors,
            mv=mv,
            effects=effects,
            string_pools=string_pools,
            subtypes_pool=subtypes_pool,
            fallback_text=DEFAULT_EQUIPMENT,
        )
        rules_parts.append("Equip {EQUIP_COST}")

    else:
        card.types = ['Land']
        # Lands have no mana cost in MTG
        card.mana_cost = ""

        # --- Enhanced Land generation ---
        # 1) Base mana ability: any one color OR any of N chosen colors (2-5 based on rarity)
        ALL_COLS = ['W','U','B','R','G']
        available = spec.colors if spec.colors else ALL_COLS
        rarity_key = (rarity or '').lower()

        # Decide how many colors this land can produce based on rarity
        def _colors_span_for_rarity(rk: str, avail_n: int) -> int:
            # common: 1-2; uncommon: 1-3; rare: 2-4; mythic: 3-5 (clamped by available colors)
            rng = {
                'common': (1, 2),
                'uncommon': (1, 3),
                'rare': (2, 4),
                'mythic': (3, 5),
            }.get(rk, (1, 2))
            hi = max(rng[0], min(rng[1], avail_n))
            lo = min(rng[0], hi)
            return random.randint(lo, hi)

        ncols = _colors_span_for_rarity(rarity_key, len(available))

        if ncols <= 1 or ncols >= 5:
            # Either strictly "any one color" or effectively five colors
            rules_parts.append("{T}: Add one mana of any color.")
        else:
            chosen = sorted(random.sample(available, k=ncols), key=lambda c: "WUBRG".index(c))
            mana_syms = [f"{{{c}}}" for c in chosen]
            if len(mana_syms) == 2:
                mana_text = f"{mana_syms[0]} or {mana_syms[1]}"
            else:
                mana_text = ", ".join(mana_syms[:-1]) + f", or {mana_syms[-1]}"
            rules_parts.append(f"{{T}}: Add {mana_text}.")

        # 2) Penalties: a grab bag such as ETB tapped or life loss.
        LAND_PENALTIES = [
            "This land enters the battlefield tapped.",
            "When this land enters the battlefield, you lose 1 life.",
            "Whenever this land becomes tapped, you lose 1 life.",
            "Whenever this land becomes tapped, it deals 1 damage to you.",
            "When this land enters the battlefield, sacrifice it unless you pay {1}.",
        ]
        # Choose number of penalties (lean heavier at lower rarities)
        penalty_counts = {
            'common': (1, 2),
            'uncommon': (1, 2),
            'rare': (1, 1),
            'mythic': (0, 1),
        }
        plo, phi = penalty_counts.get(rarity_key, (1,1))
        num_penalties = random.randint(plo, phi)
        if num_penalties > 0:
            rules_parts.extend(random.sample(LAND_PENALTIES, k=min(num_penalties, len(LAND_PENALTIES))))

        # 3) Extra abilities pulled from Enchantment/Artifact pools
        # common: 1, uncommon: 1-2, rare: 2-3, mythic: 3-4
        extra_slots_rng = {
            'common': (1, 1),
            'uncommon': (1, 2),
            'rare': (2, 3),
            'mythic': (3, 4),
        }.get(rarity_key, (1,1))
        extra_slots = random.randint(*extra_slots_rng)

        # Fill each slot by sampling either Enchantment or Artifact effect templates
        for _ in range(extra_slots):
            type_choice = random.choice(['Enchantment', 'Artifact'])
            # Use one slot at a time to force diversity and respect uniqueness
            _append_unique_effects(
                rules_parts,
                type_key=type_choice,
                slots=1,
                colors=colors,
                mv=max(1, mv),
                effects=effects,
                string_pools=string_pools,
                subtypes_pool=subtypes_pool,
            )

    # Final pass so all placeholders (including late-added lines) are substituted
    raw_text = "\n".join([p for p in rules_parts if p])
    card.rules_text = finalize_effect_template(raw_text, colors, mv, string_pools, subtypes_pool)

    return card
