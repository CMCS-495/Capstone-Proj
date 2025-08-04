from Game_Modules.import_assets import gear, enemies, game_map
from Game_Modules.import_assets import inventory as INVENTORY_POOL
from Game_Modules.import_assets import gear as GEAR_POOL
from Game_Modules.import_assets import gear as RAW_GEAR
from Game_Modules.import_assets import enemies as RAW_ENEMIES
from Game_Modules               import llm_client
from Game_Modules.map           import DungeonMap
from Game_Modules.entities      import Player
from Game_Modules import voice
import random
import threading
import os

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

# Preloaded room descriptions and spawn rolls
PRELOADED_ROOMS = {}
PRESPAWN = {}

def rebuild_player(session, player_template):
    """Reconstruct a Player object from session state + equipped gear."""
    base = player_template.get('stats', {'attack':5,'defense':3,'speed':4})
    bonuses = { stat: sum(item.get(stat,0)
                   for item in session['equipped'].values() if item)
               for stat in base }
    max_hp = player_template.get('stats', {}).get('max_health', 100)
    p = Player(
        session['player_name'],
        base['attack']  + bonuses['attack'],
        base['defense'] + bonuses['defense'],
        base['speed']   + bonuses['speed'],
        session['level'],
        session['xp'],
        max_hp
    )
    p.hp = session['hp']
    return p

def get_room_name(room_id):
    """Fetch a printable room name (falling back to the id)."""
    info = dungeon_map.rooms.get(room_id, {})
    return info.get('name', room_id)


def preload_room(room_id, session, spawn_chance=0.6, search_chance=0.5):
    """Background-preload LLM description and spawn rolls for one room."""
    if room_id not in dungeon_map.rooms:
        return

    settings = session.get('settings', {}).copy()
    def task():
        room = dungeon_map.rooms[room_id]
        if not room.get('llm_description'):
            ctx = {
                'prompt': room.get('llm_prompt', ''),
                'neighbors': room.get('neighbors', [])
            }
            length = settings.get('llm_return_length', 50)
            desc = llm_client.generate_description('room', ctx, length)
            room['llm_description'] = desc
        pre = {}
        if random.random() < spawn_chance:
            weights = [e.get('encounter_rate', 0) for e in RAW_ENEMIES]
            chosen = random.choices(RAW_ENEMIES, weights=weights, k=1)[0] if sum(weights) > 0 else random.choice(RAW_ENEMIES)
            enemy = chosen.copy()
            if not enemy.get('llm_description'):
                ctx = {'name': enemy['name'], 'level': enemy.get('level',1)}
                length = settings.get('llm_return_length', 50)
                enemy['llm_description'] = llm_client.generate_description('enemy', ctx, length)
            pre['enemy'] = enemy
        if random.random() < search_chance:
            found = random.choice(GEAR_POOL).copy()
            if not found.get('llm_description'):
                ctx = {
                    'name': found.get('name',''),
                    'stats': {k:v for k,v in found.items() if k not in ('name','type','drop_rate')}
                }
                length = settings.get('llm_return_length', 50)
                found['llm_description'] = llm_client.generate_description('gear', ctx, length)
            pre['gear'] = found
        PRESPAWN[room_id] = pre
        PRELOADED_ROOMS[room_id] = True

    threading.Thread(target=task, daemon=True).start()


def preload_neighbors(room_id, session, spawn_chance=0.6, search_chance=0.5):
    for nbr in dungeon_map.get_neighbors(room_id):
        if nbr not in PRELOADED_ROOMS:
            preload_room(nbr, session, spawn_chance, search_chance)


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

    pre = PRESPAWN.pop(tgt_room, None)
    enemy_data = pre.get('enemy') if pre else None

    # Roll for spawn
    if enemy_data:
        e = enemy_data
        msg = enemy_audio_desc(e, session)
    elif random.random() < spawn_chance:
        if enemy_data:
            e = enemy_data
        else:
            # Use encounter_rate (0–100) as weights
            weights = [e.get('encounter_rate', 0) for e in RAW_ENEMIES]
            # If all rates zero, fallback to uniform
            chosen = random.choices(RAW_ENEMIES, weights=weights, k=1)[0] if sum(weights) > 0 else random.choice(RAW_ENEMIES)
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

        msg = enemy_audio_desc(e, session)
    else:
        msg = f"You enter {get_room_name(tgt_room)}. It's quiet."

    if 'PYTEST_CURRENT_TEST' not in os.environ:
        preload_neighbors(tgt_room, session)
    return msg


# TODO Rename this here and in `move_player`
def enemy_audio_desc(e, session):
    lvl = e.get('level', 1)

    stats = e.get('stats')
    if not stats or 'health' not in stats:
        match = next((en for en in RAW_ENEMIES if en.get('name') == e.get('name')), None)
        if match:
            stats = match.get('stats', {}).copy()
            e['stats'] = stats

    base_hp = stats.get('health') if stats and 'health' in stats else 15 + (lvl - 1) * 5
    e['level'] = lvl
    e['max_hp'] = base_hp
    e['current_hp'] = base_hp

    session['enemy']     = e['name']
    session['encounter'] = e

    # Queue voice text if narration is enabled
    if session.get('settings', {}).get('voice'):
        session['encounter_voice'] = f"Enemy Encountered. {e['llm_description']}"

    return f"<b>Enemy:</b> {e['name']} — {e['llm_description']}"

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

    pre = PRESPAWN.get(session.get('room_id'), {})
    found = pre.pop('gear', None) if pre else None

    # Roll for a drop
    if found:
        return item_audio_desc(found, session)
    elif random.random() < search_chance:
        if not found:
            # Pick and copy a gear item
            found = random.choice(GEAR_POOL).copy()

        return item_audio_desc(found, session)
    return "Nothing found."


# TODO Rename this here and in `search_room`
def item_audio_desc(found, session):
    # Lazy‐generate a description
    if not found.get('llm_description'):
        ctx = {
            'name':  found.get('name',''),
            'stats': {k:v for k,v in found.items()
                      if k not in ('name','type','drop_rate')}
        }
        length = session.get('settings', {}).get('llm_return_length', 50)
        found['llm_description'] = llm_client.generate_description('gear', ctx, length)

    # Generate audio for item description if enabled
    if session.get('settings', {}).get('voice'):
        voice_name = session.get('settings', {}).get('voice_name', 'default')
        text = f"You found an item. {found['llm_description']}"
        session['voice_audio'] = voice.generate_voice(text, voice_name)

    # Append to the player's inventory
    inv = session.setdefault('inventory', [])
    inv.append(found)

    # Show name + description
    return f"Found gear: <strong>{found['name']}</strong><br>{found['llm_description']}"

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
