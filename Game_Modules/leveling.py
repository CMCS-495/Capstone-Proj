import argparse
import math
import random
try:
    from .import_assets import import_assets
    from .export_assets import export_assets
except Exception:
    import_assets = None
    export_assets = None

def xp_threshold(level):
    """
    XP needed to reach `level` based on growth rate:
      100 * log(10 / (11 - level))
    where level 1 corresponds to denominator 10 (-10 → level 1),
    up to level 10 (denominator 1). Levels ≥11 are effectively unreachable.
    """
    return float('inf') if level >= 11 else 100 * math.log(10 / (11 - level))


def _stat_gain(next_level, current_stat):
    """Return stat increase for reaching ``next_level`` from the previous one."""
    xp_needed = xp_threshold(next_level) - xp_threshold(next_level - 1)
    base = 1 if xp_needed in (0, float('inf')) else math.ceil(100 / xp_needed)
    rand_max = max(1, math.ceil(current_stat / 4))
    return base + random.randint(1, rand_max)

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
        for lvl in range(current_level + 1, new_level + 1):
            for stat in ('attack', 'defense', 'speed', 'current_health', 'max_health'):
                cur = player.get(stat, 0)
                player[stat] = cur + _stat_gain(lvl, cur)
        player['level'] = new_level

    player['xp'] = total_xp
    return new_level > current_level, player

def apply_leveling(session, player_template):
    """Update session and template based on XP, return True if level up occurs."""
    xp = session.get('xp', 0)
    current_level = session.get('level', 1)
    new_level = current_level

    while xp >= xp_threshold(new_level + 1):
        new_level += 1

    if new_level > current_level:
        for lvl in range(current_level + 1, new_level + 1):
            for stat in (
                'attack',
                'defense',
                'speed',
                'current_health',
                'max_health',
            ):
                if 'stats' in player_template:
                    stats = player_template.setdefault('stats', {})
                    cur = stats.get(stat, 0)
                    stats[stat] = cur + _stat_gain(lvl, cur)
                else:
                    cur = player_template.get(stat, 0)
                    player_template[stat] = cur + _stat_gain(lvl, cur)
        session['level'] = new_level
        max_hp = player_template.get('stats', {}).get('max_health', session.get('hp', 0))
        session['hp'] = min(session.get('hp', max_hp), max_hp)
        return True
    return False

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
