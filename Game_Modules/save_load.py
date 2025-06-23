import json
import os

def load_map_from_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "Games_Assets", "map.json")
    with open(path, "r") as f:
        return json.load(f)

def load_inventory():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "Games_Assets", "inventory.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({"items": []}, f)
    with open(path, "r") as f:
        return json.load(f)

def save_inventory(inventory):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "Games_Assets", "inventory.json")
    with open(path, "w") as f:
        json.dump(inventory, f, indent=2)
