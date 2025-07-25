import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import importlib
import types
import pytest
from Flask import flask_app
from Game_Modules import rng

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(rng, 'main', lambda: print('5'))
    monkeypatch.setattr(flask_app, 'render_template', lambda *a, **k: 'OK')
    flask_app.app.config['TESTING'] = True
    with flask_app.app.test_client() as client:
        yield client

def test_menu(client):
    resp = client.get('/')
    assert resp.status_code == 200

def test_start_game(client):
    resp = client.post('/start', data={'name': 'Hero'})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['player_name'] == 'Hero'

@pytest.mark.parametrize('diff,expected', [
    ('Easy', 100),
    ('Normal', 50),
    ('Hard', 10),
])
def test_start_game_difficulty(client, diff, expected):
    with client.session_transaction() as sess:
        sess['settings'] = {'difficulty': diff}
    resp = client.post('/start', data={'name': 'Hero'})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['hp'] == expected
        assert sess['difficulty'] == diff

@pytest.mark.parametrize('diff,expected', [
    ('Easy', 100),
    ('Normal', 50),
    ('Hard', 10),
])
def test_start_game_difficulty_form(client, diff, expected):
    resp = client.post('/start', data={'name': 'Hero', 'difficulty': diff})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['hp'] == expected
        assert sess['difficulty'] == diff

def test_rng_route(client):
    resp = client.get('/rng?min=1&max=10')
    assert resp.data.strip() == b'5'

def test_shutdown(client):
    resp = client.post('/shutdown')
    assert resp.status_code == 204

def test_minimap_caching(client):
    client.post('/start', data={'name': 'Hero'})
    client.get('/explore')
    resp = client.get('/minimap.png')
    assert resp.status_code == 200
    cache_control = resp.headers.get('Cache-Control', '')
    assert 'max-age=0' in cache_control
