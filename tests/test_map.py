import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game_Modules.map import DungeonMap

def test_init_with_list():
    data = [{'room_id': 'A', 'neighbors': ['B']}, {'room_id': 'B', 'neighbors': ['A']}]
    dm = DungeonMap(data)
    assert dm.rooms['A']['neighbors'] == ['B']

def test_is_valid_move():
    dm = DungeonMap({'A': {'neighbors': ['B']}, 'B': {'neighbors': []}})
    assert dm.is_valid_move('A', 'B')
    assert not dm.is_valid_move('A', 'C')

def test_get_neighbors_missing():
    dm = DungeonMap({'A': {'neighbors': ['B']}})
    assert dm.get_neighbors('A') == ['B']
    assert dm.get_neighbors('X') == []
