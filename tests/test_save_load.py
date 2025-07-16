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
        z.writestr('player.json', json.dumps({'name':'h','current_map_location':'A','level':1,'xp':0,'stats':{'current_health':5}}))
        z.writestr('inventory.json', json.dumps([]))
        z.writestr('map.json', json.dumps([{'room_id':'A'}]))
        z.writestr('gear.json', json.dumps({}))
        z.writestr('enemies.json', json.dumps([]))
    buf.seek(0)
    save_load.load_game_from_zip(buf, session)
    assert session['player_name'] == 'h'
    assert session['room_id'] == 'A'
    assert session['level'] == 1
    assert isinstance(session['inventory'], list)
