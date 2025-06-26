from Game_Modules.import_assets import gear, enemies, game_map
from Game_Modules.map           import DungeonMap
from Game_Modules.entities      import Player
import random

# initialize shared assets once
dungeon_map = DungeonMap(game_map)
GEAR_POOL   = gear.get('weapons', []) + gear.get('armor', []) + gear.get('boots', []) + gear.get('helmets', []) + gear.get('rings', []) + gear.get('aid', [])
ENEMIES     = enemies

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
    """Attempt to move. Updates session and returns a message."""
    current = session['room_id']

    # same-room?
    if tgt_room == current:
        return "You're already here."
    # invalid exit?
    if not dungeon_map.is_valid_move(current, tgt_room):
        return "Can't go that way."

    # perform the move
    session['room_id'] = tgt_room
    session.pop('encounter', None)
    session.pop('enemy', None)

    # maybe spawn an enemy
    if session['remaining'] and random.random() < spawn_chance:
        return _extracted_from_move_player_19(session)
    # no enemy
    return f"You enter {get_room_name(tgt_room)}. It's quiet."


# TODO Rename this here and in `move_player`
def _extracted_from_move_player_19(session):
    choice = random.choice(session['remaining'])
    e = next(x for x in ENEMIES if x.get('name') == choice).copy()
    lvl = e.get('level', 1)
    e['level'] = lvl
    e['max_hp']     = 15 + (lvl - 1) * 5
    e['current_hp'] = e['max_hp']
    session['enemy']     = e['name']
    session['encounter'] = e

    desc = e.get('description', '')  # default to empty if missing
    return f"<b>Enemy:</b> {e['name']} — {desc}"


def search_room(session, search_chance=0.5):
    """Attempt a search. Updates session['bag'] and session['searched_rooms'], returns message."""
    room = session['room_id']
    if 'encounter' in session:
        return "An enemy blocks your search!"
    if room in session['searched_rooms']:
        return "You already searched here."
    session['searched_rooms'].append(room)

    # success?
    if random.random() < search_chance and len(session['bag']) < 3:
        available = [g for g in GEAR_POOL
                     if g['type'] not in {i['type'] for i in session['bag']}]
        if not available:
            return "No more gear left."
        item = random.choice(available)
        session['bag'].append(item)
        return f"Found gear: {item['name']}"
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
