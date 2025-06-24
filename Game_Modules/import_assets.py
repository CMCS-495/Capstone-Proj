import os
import json

BASE_DIR = os.path.dirname(__file__)
NEW_ASSETS_DIR = os.path.join(BASE_DIR, 'Game_Assets')
SAVED_ASSETS_DIR = os.path.join(BASE_DIR, 'saved_game_assets')
TEMPLATES_SUBFOLDER = 'templates'

def load_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)

def import_assets(source='new'):
    """
    Load assets from either the new game assets or saved game assets.
    source: 'new' for fresh assets, 'saved' for loaded game assets.
    """
    if source == 'new':
        assets_dir = NEW_ASSETS_DIR
    elif source == 'saved':
        assets_dir = SAVED_ASSETS_DIR
    else:
        raise ValueError("source must be 'new' or 'saved'")

    templates_dir = os.path.join(assets_dir, TEMPLATES_SUBFOLDER)

    inventory = load_json_file(os.path.join(assets_dir, 'inventory.json'))
    gear = load_json_file(os.path.join(assets_dir, 'gear.json'))
    game_map = load_json_file(os.path.join(assets_dir, 'map.json'))
    enemies = load_json_file(os.path.join(assets_dir, 'enemies.json'))
    player_template = load_json_file(os.path.join(templates_dir, 'player-template.json'))

    return {
        'inventory': inventory,
        'gear': gear,
        'game_map': game_map,
        'enemies': enemies,
        'player_template': player_template,
    }

# Default: load new game assets
assets = import_assets('new')
inventory = assets['inventory']
gear = assets['gear']
game_map = assets['game_map']
enemies = assets['enemies']
player_template = assets['player_template']

__all__ = ['import_assets', 'inventory', 'gear', 'game_map', 'enemies', 'player_template']
