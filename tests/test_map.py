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
