import math


def _calc_damage(attacker, defender):
    """Return damage based on attack/defense ratio."""
    # avoid division by zero
    defense = max(1, getattr(defender, "defense", 1))
    dmg = math.ceil(getattr(attacker, "attack", 0) / defense)
    return max(1, dmg)


def player_attack(player, enemy):
    dmg = _calc_damage(player, enemy)
    enemy.take_damage(dmg)
    return f"You attack the {enemy.name} for {dmg} damage."

def enemy_attack(player, enemy):
    if not enemy.is_alive():
        return f"The {enemy.name} is defeated and cannot attack."
    dmg = _calc_damage(enemy, player)
    player.take_damage(dmg)
    return f"The {enemy.name} hits you for {dmg} damage."
