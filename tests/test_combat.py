import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
from Game_Modules.combat import _calc_damage, player_attack, enemy_attack
from Game_Modules.entities import Player, Enemy

def test_calc_damage():
    attacker = Player('A', attack=5)
    defender = Enemy('D', {'defense':2})
    assert _calc_damage(attacker, defender) == math.ceil(attacker.attack / defender.defense)

def test_player_attack_reduces_hp():
    player = Player('Hero', attack=8)
    enemy = Enemy('Goblin', {'defense':2})
    start_hp = enemy.hp
    msg = player_attack(player, enemy)
    dmg = math.ceil(player.attack / enemy.defense)
    assert enemy.hp == start_hp - dmg
    assert str(dmg) in msg

def test_enemy_attack_when_defeated():
    player = Player('Hero')
    enemy = Enemy('Goblin', {})
    enemy.hp = 0
    msg = enemy_attack(player, enemy)
    assert msg == "The Goblin is defeated and cannot attack."
