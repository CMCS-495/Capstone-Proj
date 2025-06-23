import os
import json
import import_assets

BASE_DIR = os.path.dirname(__file__)
INVENTORY_FILE = os.path.join(BASE_DIR, 'game_assets', 'inventory.json')

# loaded data from import_assets.py
inventory = import_assets.inventory           # {'UUIDs': [...]}
gear = import_assets.gear                     # {'weapons': [...], 'armor': [...], ...}

def save_inventory():
    """Persist the inventory back to inventory.json."""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)

def find_item(uuid):
    """
    Look up an item by UUID across all gear categories.
    Returns (category, item_dict) or (None, None) if not found.
    """
    for category, items in gear.items():
        for item in items:
            if item.get('UUID') == uuid:
                return category, item
    return None, None

def add_to_inventory(uuid):
    """
    Add the given UUID to the inventory (if it exists in gear and isn't already present),
    then save to disk.
    """
    cat, item = find_item(uuid)
    if not item:
        raise ValueError(f"No item with UUID {uuid!r} found in gear.")
    if uuid in inventory.get('UUIDs', []):
        return
    inventory.setdefault('UUIDs', []).append(uuid)
    save_inventory()

def remove_from_inventory(uuid):
    """
    Remove the given UUID from the inventory (if present),
    then save to disk.
    """
    uuids = inventory.get('UUIDs', [])
    if uuid not in uuids:
        return
    uuids.remove(uuid)
    save_inventory()

def display_inventory():
    """
    Print out all items in the inventory with their name, category, and stats.
    """
    uuids = inventory.get('UUIDs', [])
    if not uuids:
        print("Inventory is empty.")
        return
    for uuid in uuids:
        cat, item = find_item(uuid)
        if item:
            name = item.get('name', 'Unknown')
            stats = item.get('stats', {})
            print(f"- {name} ({cat}): {stats}")
        else:
            print(f"- Unknown item UUID: {uuid}")
