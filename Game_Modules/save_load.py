import os
import json
from . import export_assets

BASE_DIR = os.path.dirname(__file__)
SAVE_ROOT = os.path.join(BASE_DIR, 'Player_Saves')

def save_game():
    export_assets.export_assets()

def load_game():
    save_paths = []
    for player_dir in sorted(os.listdir(SAVE_ROOT)):
        dir_path = os.path.join(SAVE_ROOT, player_dir)
        if os.path.isdir(dir_path):
            save_paths.extend(
                os.path.join(dir_path, fname)
                for fname in sorted(os.listdir(dir_path))
                if fname.endswith('.json')
            )
    if not save_paths:
        print("No saves found.")
        return None
    for idx, path in enumerate(save_paths, 1):
        print(f"{idx}. {path}")
    choice = int(input("Select save to load: "))
    filepath = save_paths[choice - 1]
    with open(filepath) as f:
        data = json.load(f)
    print(f"Loaded save: {filepath}")
    return data

def load_map_from_file(path=None):
    """
    Loads the map from a JSON file.
    If no path is given, loads from the default location in Game_Assets.
    """
    if path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, 'Game_Assets', 'map.json')
    with open(path, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    print("1) Save Game")
    print("2) Load Game")
    choice = input("Choose an option: ")
    if choice == '1':
        save_game()
    elif choice == '2':
        loaded_data = load_game()
    else:
        print("Invalid option.")