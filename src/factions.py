"""
Facções (c. 280 a.C.): dados e utilitários para loja, loot e spawns.

Mantém um registro leve e funções de rolagem. Não contem lógica pesada.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from . import items


# Facção -> dados (pesos simples). IDs referenciam src/items.py
FACTIONS: Dict[str, Dict] = {
    "macedon": {
        "name": "Macedon",
        # Roxo
        "palette": {"primary": (128, 0, 128), "accent": (230, 200, 60)},
        "icon": "⚔",
        "biome": "mountain",
        "spawn_weights": {
            "phalangite": 5,
            "hoplite": 2,
            "macedon_archer": 2,
            "thracian": 1,
        },
        "shop_weights": {
            # armas
            "macedon_sarissa_t1": 4, "macedon_sarissa_t2": 3, "macedon_sarissa_t3": 1,
            "greek_xiphos_t1": 3, "greek_kopis_t2": 2,
            # proteções
            "phrygian_helmet_t1": 3, "muscled_cuirass_t2": 2, "pelte_shield_t1": 2,
        },
        "loot_weights": {
            "macedon_sarissa_t1": 3, "greek_xiphos_t1": 3, "phrygian_helmet_t1": 2,
        },
    },
    "greeks": {
        "name": "Greek City-States",
        # Azul claro
        "palette": {"primary": (100, 180, 255), "accent": (240, 240, 240)},
        "icon": "λ",
        "biome": "coastal",
        "spawn_weights": {
            "hoplite": 5,
            "phalangite": 2,
            "greek_archer": 2,
        },
        "shop_weights": {
            "greek_dory_t1": 4, "greek_dory_t2": 3,
            "aspis_shield_t2": 2,
            "corinthian_helmet_t2": 3, "illyrian_helmet_t1": 2,
            "linothorax_t2": 3,
            "greek_xiphos_t1": 3,
        },
        "loot_weights": {
            "greek_dory_t1": 3, "greek_xiphos_t1": 3, "linothorax_t2": 1,
        },
    },
    "ptolemaic": {
        "name": "Ptolemaic Egypt",
        # Verde marinho
        "palette": {"primary": (46, 139, 87), "accent": (30, 110, 90)},
        "icon": "☥",
        "biome": "desert",
        "spawn_weights": {"ptolemaic_guard": 4, "hoplite": 2, "egyptian_archer": 2},
        "shop_weights": {
            "ptolemaic_khopesh_t2": 3, "ptolemaic_spear_t1": 3,
            "ptolemaic_linen_bronze_t2": 2,
        },
        "loot_weights": {"ptolemaic_spear_t1": 3, "ptolemaic_khopesh_t2": 2},
    },
    "seleucid": {
        "name": "Seleucid / Hellenistic Persia",
        # Branco com vinho
        "palette": {"primary": (245, 245, 245), "accent": (128, 0, 32)},
        "icon": "✧",
        "biome": "steppe",
        "spawn_weights": {"cataphract": 2, "soldier": 2, "seleucid_archer": 2, "hoplite": 1},
        "shop_weights": {
            "seleucid_akinakes_t1": 3, "hellenic_sabre_t3": 1,
            "composite_bow_t2": 2, "scale_armor_t2": 2,
        },
        "loot_weights": {"seleucid_akinakes_t1": 3, "scale_armor_t2": 1},
    },
    "rome": {
        "name": "Roman Republic",
        # Vermelho
        "palette": {"primary": (180, 30, 30), "accent": (230, 200, 120)},
        "icon": "SPQR",
        "biome": "mediterranean",
        "spawn_weights": {"legionary": 5, "soldier": 2, "roman_archer": 2},
        "shop_weights": {
            "roman_gladius_t2": 4, "roman_pilum_t2": 3, "roman_scutum_t2": 3,
            "montefortino_helmet_t2": 3, "lorica_hamata_t3": 1,
        },
        "loot_weights": {"roman_gladius_t2": 3, "montefortino_helmet_t2": 2},
    },
    "carthage": {
        "name": "Carthage",
        # Branco
        "palette": {"primary": (245, 245, 245), "accent": (80, 80, 80)},
        "icon": "☩",
        "biome": "semiarid",
        "spawn_weights": {"carthaginian": 4, "soldier": 2, "carthage_archer": 2},
        "shop_weights": {
            "carthage_spear_t2": 3, "carthage_shortsword_t1": 3,
            "carthage_scale_t2": 2, "carthage_oval_shield_t1": 3,
        },
        "loot_weights": {"carthage_shortsword_t1": 3, "carthage_oval_shield_t1": 2},
    },
    "kush": {
        "name": "Kingdom of Kush",
        # Amarelo
        "palette": {"primary": (240, 200, 40), "accent": (60, 120, 50)},
        "icon": "弓",
        "biome": "savana",
        "spawn_weights": {"kush_archer": 5, "soldier": 1},
        "shop_weights": {"kush_longbow_t2": 3, "kush_spear_t1": 3, "kush_leather_t1": 3},
        "loot_weights": {"kush_spear_t1": 3, "kush_longbow_t2": 1},
    },
    "maurya": {
        "name": "Maurya",
        # Rosa
        "palette": {"primary": (255, 105, 180), "accent": (240, 170, 20)},
        "icon": "☸",
        "biome": "monsoon",
        "spawn_weights": {"maurya_spearman": 5, "soldier": 1},
        "shop_weights": {"maurya_spear_t2": 3, "maurya_composite_bow_t3": 1, "lamellar_armor_t3": 1},
        "loot_weights": {"maurya_spear_t2": 2},
    },
    "pontus": {
        "name": "Pontus",
        # Preto
        "palette": {"primary": (20, 20, 20), "accent": (180, 140, 80)},
        "icon": "⛰",
        "biome": "mountain_forest",
        "spawn_weights": {"pontic_raider": 5, "soldier": 1},
        "shop_weights": {"pontic_kopis_t2": 3, "pontic_light_lance_t1": 3, "pontic_tunic_bronze_t1": 2},
        "loot_weights": {"pontic_light_lance_t1": 3},
    },
    "thrace": {
        "name": "Thrace / Illyria",
        # Ciano
        "palette": {"primary": (0, 200, 200), "accent": (230, 230, 210)},
        "icon": "⚒",
        "biome": "rugged",
        "spawn_weights": {"thracian": 6, "bandit": 2},
        "shop_weights": {"thracian_rhomphaia_t3": 1, "balkan_light_axe_t1": 4, "balkan_simple_helm_t1": 3},
        "loot_weights": {"balkan_light_axe_t1": 3},
    },
    "bandits": {
        "name": "Bandits",
        # Cinza
        "palette": {"primary": (130, 130, 130), "accent": (200, 200, 200)},
        "icon": "☠",
        "biome": "badlands",
        "spawn_weights": {"bandit": 6, "thracian": 2},
        "shop_weights": {
            # Itens simples T1 (serão adicionados em items.py)
            "bandit_club": 5,
            "bandit_hand_axe": 3,
            "bandit_short_spear": 4,
            "bandit_dagger": 4,
            "bandit_sling": 3,
            "bandit_self_bow": 2,
            "bandit_round_shield": 4,
            "bandit_padded_cap": 3,
            "bandit_leather_vest": 3,
        },
        "loot_weights": {
            "bandit_club": 4,
            "bandit_dagger": 3,
            "bandit_padded_cap": 2,
            "bandit_leather_vest": 2,
        },
    },
}


def list_factions() -> List[str]:
    return list(FACTIONS.keys())


def get_faction(fid: str) -> Optional[Dict]:
    return FACTIONS.get(fid)


def _weighted_choice(weights: Dict[str, int]) -> Optional[str]:
    pool = [(k, int(v)) for k, v in weights.items() if int(v) > 0]
    if not pool:
        return None
    total = sum(w for _, w in pool)
    r = random.randint(1, total)
    acc = 0
    for k, w in pool:
        acc += w
        if r <= acc:
            return k
    return pool[-1][0]


def roll_enemy_type(fid: str) -> Optional[str]:
    f = get_faction(fid)
    if not f:
        return None
    return _weighted_choice(f.get("spawn_weights", {}))


def roll_shop_items(fid: str, n: int = 6) -> List[items.Item]:
    """Retorna uma lista de Items para a loja da facção."""
    f = get_faction(fid)
    if not f:
        return []
    result: List[items.Item] = []
    for _ in range(n):
        iid = _weighted_choice(f.get("shop_weights", {}))
        if iid:
            it = items.get_item_by_id(iid, with_random_quality=True)
            result.append(it)
        else:
            result.append(None)
    # Completa até n posições
    while len(result) < n:
        result.append(None)
    return result


def roll_loot(fid: str, tier_hint: int = 2, chance: float = 0.15) -> Optional[items.Item]:
    """Rola um loot simples por inimigo derrotado com chance, ponderado pela facção."""
    if random.random() >= chance:
        return None
    f = get_faction(fid)
    if not f:
        return None
    iid = _weighted_choice(f.get("loot_weights", {}))
    if not iid:
        return None
    return items.get_item_by_id(iid, with_random_quality=True)


def map_world_faction_to_faction_id(world_faction: str) -> str:
    """Mapeia 'kingdom'/'bandits' para facções internas (ajustável)."""
    wf = (world_faction or "").lower()
    # Direct match to known factions
    if wf in FACTIONS:
        return wf
    # Legacy/aliases
    if wf == "kingdom":
        return "greeks"
    if wf == "bandits":
        return "bandits"
    if wf == "monsters":
        return "monsters"
    # Fallback: return as-is to allow caller to decide (roll_loot will safely return None)
    return wf
