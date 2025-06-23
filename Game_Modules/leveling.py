import argparse
import math
import random
from import_assets import import_assets
from export_assets import export_assets

def xp_threshold(level):
    """
    XP needed to reach `level` based on growth rate:
      100 * log(10 / (11 - level))
    where level 1 corresponds to denominator 10 (-10 → level 1),
    up to level 10 (denominator 1). Levels ≥11 are effectively unreachable.
    """
    return float('inf') if level >= 11 else 100 * math.log(10 / (11 - level))

def process_level(total_xp):
    assets = import_assets('new')
    player = assets['player_template']
    current_level = player.get('level', 1)
    new_level = current_level

    # bump level while total XP meets next threshold
    while total_xp >= xp_threshold(new_level + 1):
        new_level += 1

    # if leveled up, grant random stats
    if new_level > current_level:
        for _ in range(new_level - current_level):
            for stat in ('attack', 'defense', 'speed', 'current_health', 'max_health'):
                player[stat] = player.get(stat, 0) + random.randint(1, 3)
        player['level'] = new_level

    player['xp'] = total_xp
    return new_level > current_level, player

def main():
    parser = argparse.ArgumentParser(description="Handle player leveling based on total XP")
    parser.add_argument('total_xp', type=int, help='Total XP of the player')
    args = parser.parse_args()

    leveled, player = process_level(args.total_xp)
    if leveled:
        print(f"Leveled up to level {player['level']}!")
    else:
        print(f"No level up. Current level remains at {player['level']}.")

    # save updated state back to assets
    export_assets()

if __name__ == '__main__':
    main()
