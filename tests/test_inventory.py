import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import Game_Modules.import_assets as import_assets
sys.modules.setdefault('import_assets', import_assets)
from Game_Modules import inventory

def test_find_item(monkeypatch):
    gear = {'weapons': [{'UUID': 'u1', 'name': 'Sword', 'stats': {}}]}
    monkeypatch.setattr(inventory, 'gear', gear, raising=False)
    assert inventory.find_item('u1') == ('weapons', gear['weapons'][0])
    assert inventory.find_item('bad')[0] is None

def test_add_and_remove(monkeypatch):
    gear = {'weapons': [{'UUID': 'u1', 'name': 'Sword', 'stats': {}}]}
    inv = {'UUIDs': []}
    monkeypatch.setattr(inventory, 'gear', gear, raising=False)
    monkeypatch.setattr(inventory, 'inventory', inv, raising=False)
    monkeypatch.setattr(inventory, 'save_inventory', lambda: None)
    inventory.add_to_inventory('u1')
    assert 'u1' in inv['UUIDs']
    inventory.remove_from_inventory('u1')
    assert 'u1' not in inv['UUIDs']

def test_display_inventory(monkeypatch, capsys):
    gear = {'weapons': [{'UUID': 'u1', 'name': 'Sword', 'stats': {'attack':1}}]}
    inv = {'UUIDs': ['u1']}
    monkeypatch.setattr(inventory, 'gear', gear, raising=False)
    monkeypatch.setattr(inventory, 'inventory', inv, raising=False)
    inventory.display_inventory()
    captured = capsys.readouterr().out
    assert 'Sword' in captured
