from Game_Modules.import_assets import gear, enemies, game_map
from Game_Modules.import_assets import inventory as INVENTORY_POOL
from Game_Modules.import_assets import gear as GEAR_POOL
from Game_Modules.import_assets import gear as RAW_GEAR
from Game_Modules.import_assets import enemies as RAW_ENEMIES
from Game_Modules               import llm_client
from Game_Modules.map           import DungeonMap
from Game_Modules.entities      import Player
import random

# initialize shared assets once
dungeon_map = DungeonMap(game_map)

# map each gear-category to the slot name your equip logic expects
SLOT_MAP = {
    'weapons': 'weapon',
    'armor':   'armor',
    'boots':   'boots',
    'helmets': 'helmet',
    'rings':   'ring',
    'aid':     'aid',
}

# flatten RAW_GEAR into a list, injecting a 'type' field
GEAR_POOL = []
for category, items in RAW_GEAR.items():
    slot = SLOT_MAP.get(category, category)
    for item in items:
        itm = item.copy()
        itm['type'] = slot
        GEAR_POOL.append(itm)

ENEMIES = enemies

def rebuild_player(session, player_template):
    """Reconstruct a Player object from session state + equipped gear."""
    base = player_template.get('stats', {'attack':5,'defense':3,'speed':4})
    bonuses = { stat: sum(item.get(stat,0)
                   for item in session['equipped'].values() if item)
               for stat in base }
    p = Player(
        session['player_name'],
        base['attack']  + bonuses['attack'],
        base['defense'] + bonuses['defense'],
        base['speed']   + bonuses['speed'],
        session['level'],
        session['xp']
    )
    p.hp = session['hp']
    return p

def get_room_name(room_id):
    """Fetch a printable room name (falling back to the id)."""
    info = dungeon_map.rooms.get(room_id, {})
    return info.get('name', room_id)


def move_player(session, tgt_room, spawn_chance=0.6):
    """
    Attempt to move. Each time you enter a room, with probability spawn_chance
    you'll face a random enemy drawn from RAW_ENEMIES weighted by encounter_rate.
    """
    current = session.get('room_id')
    if tgt_room == current:
        return "You're already here."
    if not dungeon_map.is_valid_move(current, tgt_room):
        return "Can't go that way."

    # Update room and clear any old encounter
    session['room_id'] = tgt_room
    session.pop('encounter', None)
    session.pop('enemy', None)
    session['searched'] = False

    # Roll for spawn
    if random.random() < spawn_chance:
        # Use encounter_rate (0–100) as weights
        weights = [e.get('encounter_rate', 0) for e in RAW_ENEMIES]
        # If all rates zero, fallback to uniform
        if sum(weights) > 0:
            chosen = random.choices(RAW_ENEMIES, weights=weights, k=1)[0]
        else:
            chosen = random.choice(RAW_ENEMIES)

        # Prepare the encounter copy
        e = chosen.copy()

        # lazy-generate description and write it back to the master list
        if not e.get('llm_description'):
            ctx = {'name': e['name'], 'level': e.get('level',1)}
            length = session.get('settings', {}).get('llm_return_length', 50)
            desc = llm_client.generate_description('enemy', ctx, length)
            e['llm_description'] = desc
            # persist into RAW_ENEMIES so your save will include it
            for master in RAW_ENEMIES:
                if master['name'] == e['name']:
                    master['llm_description'] = desc
                    break

        lvl = e.get('level', 1)
        e['level']       = lvl
        e['max_hp']      = 15 + (lvl - 1) * 5
        e['current_hp']  = e['max_hp']

        session['enemy']     = e['name']
        session['encounter'] = e

        return f"<b>Enemy:</b> {e['name']} — {e['llm_description']}"

    # No spawn
    return f"You enter {get_room_name(tgt_room)}. It's quiet."

def search_room(session, search_chance=0.5):
    """
    Attempt a search. You can only search once per visit (resets on move).
    If search succeeds, pick one gear item weighted by its drop_rate.
    """
    # can’t search in combat
    if 'encounter' in session:
        return "An enemy blocks your search!"

    # only once per visit
    if session.get('searched', False):
        return "You already searched here."

    # mark as searched for this visit
    session['searched'] = True

    # Roll for a drop
    if random.random() < search_chance:
        # Pick and copy a gear item
        found = random.choice(GEAR_POOL).copy()

        # Lazy‐generate a description
        if not found.get('llm_description'):
            ctx = {
                'name':  found.get('name',''),
                'stats': {k:v for k,v in found.items()
                          if k not in ('name','type','drop_rate')}
            }
            length = session.get('settings', {}).get('llm_return_length', 50)
            found['llm_description'] = llm_client.generate_description('gear', ctx, length)

        # Append to the player's inventory
        inv = session.setdefault('inventory', [])
        inv.append(found)

        # Show name + description
        return f"Found gear: <strong>{found['name']}</strong><br>{found['llm_description']}"

    return "Nothing found."

def process_explore_command(cmd, session,
                            player_template,
                            spawn_chance=0.6,
                            search_chance=0.5):
    """
    Given a lowercase `cmd` and the session dict, returns a 3-tuple:
      (action, endpoint, optional_message)
    """
    if cmd == 'fight' and 'encounter' in session:
        return ('redirect', 'fight', None)

    if cmd == 'run':
        session.pop('encounter', None)
        session.pop('enemy',     None)
        return ('redirect', 'explore', "You fled the fight!")

    if cmd.startswith('go '):
        raw_target = cmd.split(None, 1)[1]
        tgt = raw_target.strip().upper()
        msg = move_player(session, tgt, spawn_chance)
        return ('redirect', 'explore', msg)

    if cmd == 'search':
        msg = search_room(session, search_chance)
        return ('redirect', 'explore', msg)

    if cmd == 'inventory':
        return ('redirect', 'inventory_route', None)

    if cmd == 'save':
        return ('redirect', 'save_route',    None)

    if cmd == 'load':
        return ('redirect', 'load_route',    None)

    # default: stay on this page, no message
    return ('stay', None, None)
