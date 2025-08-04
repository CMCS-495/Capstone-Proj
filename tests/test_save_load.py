import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
import json
import zipfile
from Game_Modules import save_load

def test_load_map_from_file(tmp_path):
    data = [{'room_id': 'A'}]
    p = tmp_path / 'map.json'
    p.write_text(json.dumps(data))
    loaded = save_load.load_map_from_file(p)
    assert loaded == data

class DummySession(dict):
    modified = False

def test_load_game_from_zip(tmp_path):
    session = DummySession()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('player.json', json.dumps({
            'name': 'h',
            'current_map_location': 'A',
            'level': 1,
            'xp': 0,
            'stats': {
                'current_health': 5,
                'attack': 7,
                'defense': 3,
                'speed': 2
            }
        }))
        z.writestr('inventory.json', json.dumps([]))
        z.writestr('map.json', json.dumps([{'room_id': 'A'}]))
        z.writestr('gear.json', json.dumps({}))
        z.writestr('enemies.json', json.dumps([]))
        z.writestr('settings.json', json.dumps({'difficulty': 'Normal'}))
    buf.seek(0)
    save_load.load_game_from_zip(buf, session)
    assert session['player_name'] == 'h'
    assert session['room_id'] == 'A'
    assert session['level'] == 1
    assert isinstance(session['inventory'], list)
    assert session['settings']['difficulty'] == 'Normal'
    from Game_Modules import import_assets
    assert import_assets.player_template['stats']['attack'] == 7
    assert import_assets.player_template['stats']['defense'] == 3
    assert import_assets.player_template['stats']['speed'] == 2


def test_load_game_from_zip_equipped_names(tmp_path):
    session = DummySession()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('player.json', json.dumps({
            'name': 'h',
            'current_map_location': 'A',
            'level': 1,
            'xp': 0,
            'stats': {
                'current_health': 5,
                'attack': 7,
                'defense': 3,
                'speed': 2
            },
            'Equipped': {'weapon': 'Sword'}
        }))
        z.writestr('inventory.json', json.dumps([]))
        z.writestr('map.json', json.dumps([{'room_id': 'A'}]))
        z.writestr('gear.json', json.dumps({'Sword': {'name': 'Sword', 'type': 'weapon', 'attack': 5}}))
        z.writestr('enemies.json', json.dumps([]))
        z.writestr('settings.json', json.dumps({}))
    buf.seek(0)
    save_load.load_game_from_zip(buf, session)
    assert session['equipped']['weapon']['name'] == 'Sword'
    assert session['equipped']['weapon']['attack'] == 5
