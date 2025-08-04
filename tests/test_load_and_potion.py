import os, sys, json, zipfile
from io import BytesIO
import pytest
from Flask import flask_app
from Game_Modules import rng, voice, save_load, import_assets

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(rng, 'main', lambda: print('5'))
    monkeypatch.setattr(flask_app, 'render_template', lambda *a, **k: 'OK')
    monkeypatch.setattr(voice, 'generate_voice', lambda *a, **k: 'audio.wav')
    flask_app.app.config['TESTING'] = True
    with flask_app.app.test_client() as client:
        yield client

def make_save():
    player = {
        "name": "Hero",
        "stats": {"attack": 7, "defense": 4, "speed": 3, "current_health": 20, "max_health": 30},
        "level": 2,
        "xp": 50,
        "current_map_location": "R1_1",
        "Equipped": {},
        "rooms_cleared": ["R1_1"]
    }
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('player.json', json.dumps(player))
        z.writestr('inventory.json', json.dumps([]))
        z.writestr('map.json', json.dumps([]))
        z.writestr('gear.json', json.dumps({}))
        z.writestr('enemies.json', json.dumps([]))
        z.writestr('settings.json', json.dumps({}))
    buf.seek(0)
    return buf

def test_load_game_restores_stats_and_rooms(client):
    orig_pt = import_assets.player_template.copy()
    orig_inv = import_assets.inventory.copy()
    orig_map = dict(import_assets.game_map)
    orig_gear = import_assets.gear.copy()
    orig_enemies = list(import_assets.enemies)
    orig_settings = import_assets.settings.copy()
    buf = make_save()
    with client.session_transaction() as sess:
        sess.clear()
        save_load.load_game_from_zip(buf, sess)
        assert sess['hp'] == 20
        assert sess['rooms_cleared'] == ['R1_1']
        assert import_assets.player_template['stats']['max_health'] == 30
    import_assets.player_template.clear(); import_assets.player_template.update(orig_pt)
    import_assets.inventory.clear(); import_assets.inventory.update(orig_inv)
    import_assets.game_map.clear(); import_assets.game_map.update(orig_map)
    import_assets.gear.clear(); import_assets.gear.update(orig_gear)
    import_assets.enemies.clear(); import_assets.enemies.extend(orig_enemies)
    import_assets.settings.clear(); import_assets.settings.update(orig_settings)
    with client.session_transaction() as sess:
        sess.clear()

def test_use_potion_heals_player(monkeypatch, client):
    monkeypatch.setattr(flask_app, 'enemy_attack', lambda p, e: '')
    with client.session_transaction() as sess:
        sess.clear()
        sess['player_name'] = 'Hero'
        sess['hp'] = 5
        sess['level'] = 1
        sess['xp'] = 0
        sess['inventory'] = [{'name': 'Potion', 'type': 'aid', 'health': 5}]
        sess['equipped'] = {'weapon': None, 'shield': None, 'armor': None, 'boots': None, 'ring': None, 'helmet': None}
        sess['encounter'] = {
            'name': 'Goblin',
            'stats': {'attack': 1, 'defense': 1, 'speed': 1},
            'level': 1,
            'current_hp': 5,
            'max_hp': 5
        }
    flask_app.player_template['stats']['max_health'] = 10
    resp = client.post('/fight', data={'action': 'potion', 'potion_index': 0})
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess['hp'] == 10
        assert sess['inventory'] == []
    with client.session_transaction() as sess:
        sess.clear()
