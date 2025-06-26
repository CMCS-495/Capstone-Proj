import os
import json

# Base directories
MODULE_DIR   = os.path.dirname(__file__)
ASSETS_DIR   = os.path.join(MODULE_DIR, 'Game_Assets')
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, '..'))

def load_json_file(filename):
    """Search recursively under ASSETS_DIR, then fallback to MODULE_DIR and PROJECT_ROOT."""
    # 1) Recursive search in Game_Assets
    if os.path.isdir(ASSETS_DIR):
        for root, dirs, files in os.walk(ASSETS_DIR):
            if filename in files:
                path = os.path.join(root, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
    # 2) Top-level fallback
    for base in (MODULE_DIR, PROJECT_ROOT):
        path = os.path.join(base, filename)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    raise FileNotFoundError(f"Asset file '{filename}' not found under {ASSETS_DIR} or fallback dirs")

# Load raw JSON data
_raw_inventory       = load_json_file('inventory.json')
_raw_gear            = load_json_file('gear.json')
_raw_game_map        = load_json_file('map.json')
_raw_enemies         = load_json_file('enemies.json')
_raw_player_template = load_json_file('player-template.json')

# Process assets
inventory       = _raw_inventory
gear            = _raw_gear

# Convert game_map list into dict by room id for easier lookup
try:
    game_map = { room['room_id']: room for room in _raw_game_map }
except (TypeError, KeyError):
    # If already a dict or malformed, leave as is
    game_map = _raw_game_map

enemies         = _raw_enemies
player_template = _raw_player_template

__all__ = [
    'inventory',
    'gear',
    'game_map',
    'enemies',
    'player_template'
]
