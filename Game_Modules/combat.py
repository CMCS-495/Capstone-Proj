def player_attack(player, enemy):
    dmg = max(1, player.attack - enemy.defense)
    enemy.take_damage(dmg)
    return f"You attack the {enemy.name} for {dmg} damage."

def enemy_attack(player, enemy):
    if not enemy.is_alive():
        return f"The {enemy.name} is defeated and cannot attack."
    dmg = max(1, enemy.attack - player.defense)
    player.take_damage(dmg)
    return f"The {enemy.name} hits you for {dmg} damage."
