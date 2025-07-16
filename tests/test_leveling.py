import math
from Game_Modules import leveling


def test_xp_threshold_increases():
    assert leveling.xp_threshold(1) < leveling.xp_threshold(2)


def test_apply_leveling(monkeypatch):
    xp_needed = leveling.xp_threshold(2) + 1
    session = {'xp': xp_needed, 'level': 1, 'hp': 5}
    template = {'stats': {'max_health': 10}}
    monkeypatch.setattr(leveling.random, 'randint', lambda a,b: 1)
    leveled = leveling.apply_leveling(session, template)
    assert leveled
    assert session['level'] > 1
    assert session['hp'] <= template['stats']['max_health']
