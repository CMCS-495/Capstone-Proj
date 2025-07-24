import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import types
from unittest.mock import patch
import random
from Game_Modules import game_utils
from Game_Modules.map import DungeonMap


def setup_basic(monkeypatch):
    # simple map with two rooms
    dm = DungeonMap({'A': {'name': 'RoomA', 'neighbors': ['B']}, 'B': {'name': 'RoomB', 'neighbors': ['A']}})
    monkeypatch.setattr(game_utils, 'dungeon_map', dm, raising=False)
    monkeypatch.setattr(game_utils.llm_client, 'generate_description', lambda *a, **k: 'desc')
    monkeypatch.setattr(game_utils, 'RAW_ENEMIES', [{'name':'gob','stats':{},'level':1,'encounter_rate':100}])
    monkeypatch.setattr(game_utils, 'GEAR_POOL', [{'name':'potion','type':'aid','drop_rate':1,'llm_description':'desc'}])

def test_rebuild_player(monkeypatch):
    setup_basic(monkeypatch)
    session = {'player_name':'h','equipped':{'weapon':{'attack':2,'defense':1,'speed':1}},'level':1,'xp':0,'hp':5}
    template = {'stats':{'attack':3,'defense':3,'speed':3}}
    p = game_utils.rebuild_player(session, template)
    assert p.attack == 5  # 3 + 2
    assert p.defense == 4
    assert p.speed == 4
    assert p.hp == 5

def test_get_room_name(monkeypatch):
    setup_basic(monkeypatch)
    assert game_utils.get_room_name('A') == 'RoomA'
    assert game_utils.get_room_name('X') == 'X'

def test_move_player_spawn(monkeypatch):
    setup_basic(monkeypatch)
    session = {'room_id':'A'}
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    msg = game_utils.move_player(session, 'B', spawn_chance=1.0)
    assert 'Enemy:' in msg
    assert session['room_id'] == 'B'
    assert 'encounter' in session

def test_move_player_spawn_voice(monkeypatch):
    setup_basic(monkeypatch)
    session = {'room_id': 'A', 'settings': {'voice': True, 'voice_name': 'en'}}
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(game_utils.voice, 'generate_voice', lambda t, l: 'audio.wav')
    msg = game_utils.move_player(session, 'B', spawn_chance=1.0)
    assert 'Enemy:' in msg
    assert session['voice_audio'] == 'audio.wav'

def test_move_player_no_spawn(monkeypatch):
    setup_basic(monkeypatch)
    session = {'room_id':'A'}
    monkeypatch.setattr(random, 'random', lambda: 1.0)
    msg = game_utils.move_player(session, 'B', spawn_chance=0.0)
    assert msg == "You enter RoomB. It's quiet."
    assert session['room_id'] == 'B'

def test_search_room_found(monkeypatch):
    setup_basic(monkeypatch)
    session = {'searched': False, 'inventory': []}
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    msg = game_utils.search_room(session, search_chance=1.0)
    assert 'Found gear' in msg
    assert session['inventory']

def test_process_explore_command(monkeypatch):
    setup_basic(monkeypatch)
    session = {}
    monkeypatch.setattr(game_utils, 'move_player', lambda s,t,spawn_chance: 'moved')
    monkeypatch.setattr(game_utils, 'search_room', lambda s,ch: 'searched')
    assert game_utils.process_explore_command('inventory', session, {}) == ('redirect','inventory_route', None)
    assert game_utils.process_explore_command('go B', session, {})[0] == 'redirect'
    assert game_utils.process_explore_command('search', session, {})[0] == 'redirect'
    assert game_utils.process_explore_command('unknown', session, {}) == ('stay', None, None)
