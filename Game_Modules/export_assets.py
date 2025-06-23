import os
import json
from datetime import datetime
import import_assets

BASE_DIR = os.path.dirname(__file__)
SAVE_ROOT = os.path.join(BASE_DIR, 'Player_Saves')

def export_assets():
    # Get the player name from the loaded assets
    player_name = import_assets.player_template.get('name', 'unknown_player')
    # Ensure the player-specific save directory exists
    player_dir = os.path.join(SAVE_ROOT, player_name)
    os.makedirs(player_dir, exist_ok=True)

    # Create timestamp down to the second
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # Build the save filename
    filename = f"{player_name}-{timestamp}.json"
    filepath = os.path.join(player_dir, filename)

    # Gather all assets into one dict
    data = {
        'player': import_assets.player_template,
        'inventory': import_assets.inventory,
        'gear': import_assets.gear,
        'map': import_assets.game_map,
        'enemies': import_assets.enemies,
    }

    # Write out the combined save file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Assets exported to {filepath}")

if __name__ == "__main__":
    export_assets()
