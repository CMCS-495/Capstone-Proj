from flask import (
    Flask, render_template, request,
    redirect, session, url_for, send_file, flash
)
import os, sys, io, time, zipfile, json, random, math

# ensure Game_Modules package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game_Modules.import_assets import inventory, gear, game_map, enemies, player_template
from Game_Modules import llm_client
from Game_Modules.save_load   import save_game
from Game_Modules import save_load
from Game_Modules.export_assets import SAVE_ROOT
from Game_Modules.entities import Player, Enemy
from Game_Modules.combat import player_attack, enemy_attack
from Game_Modules.leveling import apply_leveling, xp_threshold
from Game_Modules.game_utils import (
    rebuild_player,
    get_room_name,
    process_explore_command,
    dungeon_map,
    preload_room,
    preload_neighbors,
    PRESPAWN,
    PRELOADED_ROOMS,
)

from Game_Modules import rng, save_load
from Game_Modules import voice, temp_utils
from Game_Modules.voice import available_voices


# Explicitly point Flask to the capitalized Templates directory so the
# application can locate HTML templates when running on case-sensitive
# file systems.
app = Flask(__name__, template_folder='Templates', static_folder='static')
app.secret_key = os.urandom(24)

@app.route('/voice/<path:filename>')
def voice_file(filename):
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    path = os.path.join(temp_utils.VOICE_DIR, safe_filename)
    return send_file(path, mimetype='audio/mpeg')

@app.route('/minimap.png')
def minimap_png():
    path = os.path.join(temp_utils.MAP_DIR, 'minimap.png')
    if not os.path.exists(path):
        from flask import abort
        abort(404, description="Minimap image not found.")
    return send_file(path, mimetype='image/png', max_age=0)

# Precompute ROOM_NAMES mapping for templates
ROOM_NAMES = {rid: get_room_name(rid) for rid in dungeon_map.rooms.keys()}
VOICE_CHOICES = available_voices()

# ----- MAIN MENU -----
@app.route('/')
def menu():
    current = session.get('settings', {}).get('difficulty', 'Normal')
    if not app.config.get('TESTING'):
        start_room = player_template.get('start_room', 'R1_1')
        preload_room(start_room, session)
    return render_template('menu.html', current=current)

@app.route('/reset', methods=['GET', 'POST'])
def reset_session():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('menu'))
    return render_template('reset.html')

@app.route('/start', methods=['POST'])
def start_game():
    """Begin a new game using the selected difficulty settings."""
    # Difficulty may come from a form field or previous settings
    form_diff = request.form.get('difficulty')
    settings  = session.get('settings', {})
    diff      = form_diff or settings.get('difficulty', 'Normal')
    music     = settings.get('music', True)
    llm_len   = settings.get('llm_return_length', 50)
    voice     = settings.get('voice', True)
    voice_name = settings.get('voice_name', 'default')
    map_size  = settings.get('map_size', 'Medium')
    hide_map  = settings.get('hide_minimap', False)
    theme     = settings.get('display_theme', 'Standard')
    llm_device = settings.get('llm_device', 'cpu')
    session.clear()
    PRESPAWN.clear()
    session['settings'] = {
        'difficulty': diff,
        'music': music,
        'llm_return_length': llm_len,
        'voice': voice,
        'voice_name': voice_name,
        'map_size': map_size,
        'hide_minimap': hide_map,
        'display_theme': theme,
        'llm_device': llm_device,
    }
    llm_client.set_device(llm_device)

    # Determine starting HP from difficulty
    hp_map = {'easy': 100, 'normal': 50, 'hard': 10}
    start_hp = hp_map.get(diff.lower(), 50)

    # Update player template HP values before the game begins
    stats = player_template.setdefault('stats', {})
    stats['current_health'] = start_hp
    stats['max_health'] = start_hp

    # Grab the name the user entered; if they submitted nothing, fall back to the template default
    player_name = request.form.get('name', '').strip() or player_template.get('name', 'Adventurer')

    session.update({
        'player_name': player_name,
        'room_id':      player_template.get('start_room', 'R1_1'),
        'level':        player_template.get('level', 1),
        'xp':           player_template.get('xp', 0),
        'hp':           start_hp,
        'difficulty':   diff,
        'equipped':     {
            'weapon': None, 'shield': None, 'armor': None,
            'boots':  None, 'ring':   None, 'helmet': None
        },
        'inventory':    [],
        'visited':      [],
    })
    dungeon_map.randomize_rooms(session['room_id'], pct=0)
    return redirect(url_for('explore'))

# ----- RNG -----
@app.route('/rng')
def rng_route():
    low = int(request.args.get('min', 0))
    high = int(request.args.get('max', 100))
    _argv_orig = sys.argv
    sys.argv = [sys.argv[0], str(low), str(high)]
    buf = io.StringIO()
    _stdout_orig = sys.stdout
    sys.stdout = buf
    try:
        rng.main()
    finally:
        sys.stdout = _stdout_orig
        sys.argv = _argv_orig
    return buf.getvalue().strip(), 200, {'Content-Type': 'text/plain'}

# ----- SAVE & LOAD -----@app.route('/save_as', methods=['POST'])

@app.route('/save-as', methods=['GET', 'POST'])
def save_as():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    player_name = session['player_name']
    timestamp = time.strftime("%Y%m%d%H%M%S")
    default_name = f"{player_name}-{timestamp}.zip"

    if request.method == 'POST':
        # what the user typed as zip filename
        desired = request.form['filename'].strip()
        if not desired.lower().endswith('.zip'):
            desired += '.zip'

        # safe-equipped extraction
        eq = session.get('equipped', {})
        def item_name(slot):
            it = eq.get(slot)
            return it['name'] if isinstance(it, dict) and 'name' in it else ''

        player_data = {
            "name": session['player_name'],
            "stats": {
                "attack":         player_template['stats'].get('attack',1)
                                    + sum(i.get('attack',0) for i in eq.values() if i),
                "defense":        player_template['stats'].get('defense',1)
                                    + sum(i.get('defense',0) for i in eq.values() if i),
                "speed":          player_template['stats'].get('speed',1)
                                    + sum(i.get('speed',0) for i in eq.values() if i),
                "current_health": session.get('hp', 0),
                "max_health":     player_template['stats'].get('max_health', session.get('hp',0))
            },
            "level":                session.get('level',1),
            "xp":                   session.get('xp',0),
            "current_map_location": session.get('room_id',''),
            "Equipped": {
                "weapon": item_name('weapon'),
                "armor":  item_name('armor'),
                "boots":  item_name('boots'),
                "ring":   item_name('ring'),
                "helmet": item_name('helmet')
            }
        }

        # Create ZIP in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('player.json',    json.dumps(player_data, indent=2))
            z.writestr('enemies.json',   json.dumps(enemies,      indent=2))
            z.writestr('gear.json',      json.dumps(gear,         indent=2))
            player_inv = session.get('inventory', [])
            z.writestr('inventory.json', json.dumps(player_inv,   indent=2))
            raw_map = list(game_map.values()) if isinstance(game_map, dict) else game_map
            z.writestr('map.json',       json.dumps(raw_map,     indent=2))
            if os.path.isdir(temp_utils.VOICE_DIR):
                for fname in os.listdir(temp_utils.VOICE_DIR):
                    fp = os.path.join(temp_utils.VOICE_DIR, fname)
                    if os.path.isfile(fp):
                        z.write(fp, f"voice/{fname}")
            else:
                print(f"Warning: VOICE_DIR '{temp_utils.VOICE_DIR}' does not exist or is not accessible.")
            if os.path.isdir(temp_utils.MAP_DIR):
                for fname in os.listdir(temp_utils.MAP_DIR):
                    fp = os.path.join(temp_utils.MAP_DIR, fname)
                    if os.path.isfile(fp):
                        z.write(fp, f"map/{fname}")
            else:
                # Log a warning or handle the missing directory gracefully
                print(f"Warning: Directory {temp_utils.MAP_DIR} does not exist or is inaccessible.")
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name=desired,
            mimetype='application/zip'
        )

    # GET → show the form
    return render_template(
        'save_as.html',
        player_name=player_name,
        timestamp=timestamp,
        default_name=default_name
    )

@app.route('/load_save', methods=['POST'])
def load_save():
    file = request.files.get('save_file')
    if not (file and file.filename.endswith('.zip')):
        flash("Please upload a .zip save file.", "error")
        return redirect(url_for('load_save'))
    try:
        PRESPAWN.clear()
        PRELOADED_ROOMS.clear()
        save_load.load_game_from_zip(file.stream, session)
        flash("Save loaded successfully.", "success")
        return redirect(url_for('explore'))
    except Exception as e:
        flash(f"Failed to load save: {e}", "error")
        return redirect(url_for('load_save'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Persist difficulty and other toggles in session
    if request.method == 'POST':
        diff      = request.form.get('difficulty')
        music     = request.form.get('music') == 'on'
        llm_val   = request.form.get('llm_return_length', '').strip()
        llm_device = request.form.get('llm_device', 'cpu')
        try:
            llm_len = int(llm_val)
        except (TypeError, ValueError):
            llm_len = session.get('settings', {}).get('llm_return_length', 50)
        else:
            llm_len = max(15, min(100, llm_len))
        voice     = request.form.get('voice') == 'on'
        voice_name = request.form.get('voice_name', 'default')
        map_size  = request.form.get('map_size')
        hide_map  = request.form.get('hide_minimap') == 'on'
        theme     = request.form.get('display_theme')

        session['settings'] = session.get('settings', {})
        session['settings'].update({
            'difficulty': diff,
            'music': music,
            'llm_return_length': llm_len,
            'voice': voice,
            'voice_name': voice_name,
            'map_size': map_size,
            'hide_minimap': hide_map,
            'display_theme': theme,
            'llm_device': llm_device,
        })
        llm_client.set_device(llm_device)
        flash(f"Difficulty set to {diff}", "success")
        return redirect(url_for('menu'))

    # On GET, show the form with current settings
    s = session.get('settings', {})
    return render_template(
        'settings.html',
        current=s.get('difficulty', 'Normal'),
        music_enabled=s.get('music', True),
        llm_length=s.get('llm_return_length', 50),
        voice_enabled=s.get('voice', True),
        voice_name=s.get('voice_name', 'default'),
        voice_choices=VOICE_CHOICES,
        map_size=s.get('map_size', 'Medium'),
        hide_minimap=s.get('hide_minimap', False),
        display_theme=s.get('display_theme', 'Standard'),
        llm_device=s.get('llm_device', 'cpu')
    )

# ----- EXPLORE -----
@app.route('/explore', methods=['GET','POST'])
def explore():
    # 1) Ensure in-game
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    # 2) Handle any POSTed command
    if request.method == 'POST':
        cmd = request.form.get('command','').strip().lower()
        diff = session.get('settings', {}).get('difficulty', 'Normal').lower()
        spawn_table = {'easy': 0.3, 'normal': 0.6, 'hard': 1.0}
        spawn_chance = spawn_table.get(diff, 0.6)
        action, endpoint, msg = process_explore_command(
            cmd, session, player_template, spawn_chance=spawn_chance
        )
        if msg:
            session['last_msg'] = msg
        if action == 'redirect' and endpoint:
            return redirect(url_for(endpoint))
        if action == 'fight':
            return redirect(url_for('fight'))
        return redirect(url_for('explore'))

    # 3) Rebuild Player stats
    base   = player_template['stats']
    eq     = session.get('equipped', {})
    bonus  = {
        'attack':  sum(i.get('attack',0)  for i in eq.values() if i),
        'defense': sum(i.get('defense',0) for i in eq.values() if i),
        'speed':   sum(i.get('speed',0)   for i in eq.values() if i),
    }
    from Game_Modules.entities import Player
    max_hp = player_template.get('stats', {}).get('max_health', 100)
    player = Player(
        session['player_name'],
        base.get('attack',1)  + bonus['attack'],
        base.get('defense',1) + bonus['defense'],
        base.get('speed',1)   + bonus['speed'],
        session.get('level',1),
        session.get('xp',0),
        max_hp
    )
    player.hp = session.get('hp', player.hp)

    # XP needed for next level
    xp_next = max(0, int(xp_threshold(player.level + 1) - session.get('xp', 0)))

    # 4) Lazy-generate room description
    room_id = session['room_id']
    room    = game_map[room_id]
    if not room.get('llm_description'):
        ctx = {
            'prompt': room.get('llm_prompt', ''),
            'neighbors': room.get('neighbors', [])
        }
        length = session.get('settings', {}).get('llm_return_length', 50)
        room['llm_description'] = llm_client.generate_description('room', ctx, length)

    # Trigger voice narration
    if session.get('settings', {}).get('voice'):
        visited = session.setdefault('visited', [])
        first_visit = room_id not in visited
        if first_visit:
            visited.append(room_id)
            session['visited'] = visited
        voice_name = session.get('settings', {}).get('voice_name', 'default')
        parts = []
        if first_visit:
            parts.append(room['llm_description'])
        if 'encounter_voice' in session:
            parts.append(session.pop('encounter_voice'))
        if parts:
            session['voice_audio'] = voice.generate_voice(' '.join(parts), voice_name)

    settings = session.get('settings', {})
    show_minimap = not settings.get('hide_minimap')

    # 4.5) Generate/update minimap image for current position
    if show_minimap:
        from Game_Modules.MiniMap import generate_minimap
        x = room.get('MiniMapX', 0)
        y = room.get('MiniMapy', 0)
        minimap_path = os.path.join(temp_utils.MAP_DIR, 'minimap.png')
        width, height = 300, 600
        _, marker_x, marker_y = generate_minimap(
            x, y, view_width=width, view_height=height,
            output_path=minimap_path, return_coords=True, full_map=True
        )
        marker_x_pct = marker_x / width * 100
        marker_y_pct = marker_y / height * 100

    if not app.config.get('TESTING'):
        diff = session.get('settings', {}).get('difficulty', 'Normal').lower()
        spawn_table = {'easy': 0.3, 'normal': 0.6, 'hard': 1.0}
        spawn_chance = spawn_table.get(diff, 0.6)
        preload_neighbors(room_id, session, spawn_chance)

    # 5) Build neighbor list & names map
    neighbors = dungeon_map.get_neighbors(room_id)
    ROOM_NAMES = {rid: r.get('name',rid) for rid,r in game_map.items()}

    # 6) Pull a one-time message and potion count
    response = session.pop('last_msg','')
    potions  = len([i for i in session.get('inventory',[]) if i.get('type')=='aid'])
    audio_file = session.pop('voice_audio', None)

    # 7) Render with **xp** and **player.name** guaranteed in context
    return render_template('explore.html',
        player_name      = session['player_name'],
        player           = player,
        xp               = session.get('xp', 0),
        xp_to_next       = xp_next,
        room_name        = room.get('name', room_id),
        room_description = room['llm_description'],
        gear             = eq,
        artifacts        = session.get('artifacts', []),
        neighbors        = neighbors,
        enemy            = session.get('encounter'),
        response         = response,
        potions          = potions,
        ROOM_NAMES       = ROOM_NAMES,
        audio_file       = audio_file,
        show_minimap     = show_minimap,
        marker_x         = marker_x_pct if show_minimap else 50,
        marker_y         = marker_y_pct if show_minimap else 50
    )

# ----- FIGHT -----
@app.route('/fight', methods=['GET', 'POST'])
def fight():
    if 'player_name' not in session or 'encounter' not in session:
        return redirect(url_for('explore'))

    # Rebuild the enemy
    e_data = session['encounter']
    enemy = Enemy(e_data['name'], e_data['stats'], e_data['level'])
    enemy.hp     = e_data['current_hp']
    enemy.max_hp = e_data['max_hp']

    # Rebuild the player
    base = player_template.get('stats', {'attack':10,'defense':5,'speed':5})
    bonus = {k: sum(item.get(k,0) for item in session['equipped'].values() if item) for k in base}
    max_hp = player_template.get('stats', {}).get('max_health', 100)
    player = Player(
        session['player_name'],
        base['attack']  + bonus['attack'],
        base['defense'] + bonus['defense'],
        base['speed']   + bonus['speed'],
        session['level'],
        session['xp'],
        max_hp
    )
    player.hp = session['hp']

    # Count aid items in inventory as "potions"
    inv = session.setdefault('inventory', [])
    aid_items = [i for i in inv if i.get('type') == 'aid']
    potions = len(aid_items)

    messages = []

    if request.method == 'POST':
        action = request.form['action']
        difficulty = session.get('settings', {}).get('difficulty', 'Normal')

        # Drink an aid item if available
        if action == 'potion' and potions > 0:
            for idx, itm in enumerate(inv):
                if itm.get('type') == 'aid':
                    item = inv.pop(idx)
                    break
            else:
                item = None

            potions -= 1
            heal_amount = item.get('health', 20) if item else 20
            max_hp = player_template.get('stats', {}).get('max_health', 100)
            player.hp = min(player.hp + heal_amount, max_hp)
            messages.append(f"You use an aid item and recover {heal_amount} HP.")

        if action == 'attack':
            if player.speed >= enemy.speed:
                messages.append(player_attack(player, enemy))
                if enemy.is_alive():
                    messages.append(enemy_attack(player, enemy))
            else:
                messages.append(enemy_attack(player, enemy))
                if player.hp > 0:
                    messages.append(player_attack(player, enemy))
        elif action == 'run':
            if difficulty.lower() in ('normal', 'hard'):
                messages.append(enemy_attack(player, enemy))
                if player.hp <= 0:
                    session['hp'] = player.hp
                    return render_template('fight.html',
                                           outcome='defeat',
                                           player=player,
                                           enemy=e_data,
                                           messages=messages,
                                           potions=potions)
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['hp'] = player.hp
            session['inventory'] = inv
            session['last_msg'] = "You fled!"
            return redirect(url_for('explore'))
        else:
            if enemy.is_alive():
                messages.append(enemy_attack(player, enemy))

        # Update session state
        session['hp']                  = max(player.hp, 0)
        session['encounter']['current_hp'] = max(enemy.hp, 0)
        session['inventory']           = inv

        # Check for defeat
        if player.hp <= 0:
            return render_template('fight.html',
                                   outcome='defeat',
                                   player=player,
                                   enemy=e_data,
                                   messages=messages,
                                   potions=potions)

        # Check for victory
        if not enemy.is_alive():
            return redirect(url_for('artifact'))

        return render_template('fight.html',
                               outcome='ongoing',
                               player=player,
                               enemy=e_data,
                               messages=messages,
                               potions=potions)

    # GET request: show fight screen
    return render_template('fight.html',
                           outcome='ongoing',
                           player=player,
                           enemy=e_data,
                           messages=messages,
                           potions=potions)


# ----- ARTIFACT -----
@app.route('/artifact')
def artifact():
    # Only called after win
    if 'encounter' not in session:
        return redirect(url_for('explore'))

    # Pull and clear the encounter
    e_data = session.pop('encounter')
    session.pop('enemy', None)

    # XP gain based on level ratio and enemy difficulty
    lvl = session.get('level', 1)
    xp_needed = xp_threshold(lvl + 1) - xp_threshold(lvl)
    ratio = lvl / xp_needed if xp_needed else 0
    base_stats = player_template.get('stats', {})
    eq = session.get('equipped', {})
    atk = base_stats.get('attack', 1) + sum(i.get('attack', 0) for i in eq.values() if i)
    enemy_hp = e_data.get('max_hp', 1)
    rand_max = max(1, math.ceil(enemy_hp / max(1, atk)))
    xp_gain = math.ceil(ratio + random.randint(1, rand_max))
    # Award XP and check for level ups
    session['xp'] = session.get('xp', 0) + xp_gain
    leveled = apply_leveling(session, player_template)

    if leveled:
        session['last_msg'] = (
            f"You gained {xp_gain} XP and reached level {session['level']}!"
        )
    else:
        session['last_msg'] = f"You gained {xp_gain} XP!"

    cleared = set(session.get('rooms_cleared', []))
    current_room = session.get('room_id')
    if current_room:
        cleared.add(current_room)
    session['rooms_cleared'] = list(cleared)
    if len(cleared) >= len(game_map):
        return render_template('complete.html')

    return redirect(url_for('explore'))

# ----- INVENTORY -----
@app.route('/inventory', methods=['GET','POST'])
def inventory_route():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    # Handle POST actions first
    if request.method == 'POST':
        action     = request.form.get('action')
        idx        = request.form.get('item_index', type=int)
        slot       = request.form.get('slot')

        inv = session.setdefault('inventory', [])
        eq  = session.setdefault('equipped', {
            'weapon': None,
            'armor':  None,
            'boots':  None,
            'ring':   None,
            'helmet': None
        })

        # Equip or Unequip share the same item_index
        if action in ('equip', 'unequip') and 0 <= idx < len(inv):
            item = inv[idx]
            slot = item['type']
            eq[slot] = item if action == 'equip' else None
        elif action == 'use' and 0 <= idx < len(inv):
            if inv[idx].get('type') == 'aid':
                item = inv.pop(idx)
                heal = item.get('health', 0)
                max_hp = player_template.get('stats', {}).get('max_health', session.get('hp', 0))
                session['hp'] = min(session.get('hp', 0) + heal, max_hp)

        elif action == 'drop' and 0 <= idx < len(inv):
            inv.pop(idx)

        # write back
        session['inventory'] = inv
        session['equipped']  = eq
        session.modified     = True
        return redirect(url_for('inventory_route'))

    # Build a player dict with live stats
    base_stats = player_template.get('stats', {})
    eq         = session.get('equipped', {})
    bonus_atk  = sum(i.get('attack',0)  for i in eq.values() if i)
    bonus_def  = sum(i.get('defense',0) for i in eq.values() if i)
    bonus_spd  = sum(i.get('speed',0)   for i in eq.values() if i)

    player = {
        'name':  session.get('player_name'),
        'level': session.get('level'),
        'xp':    session.get('xp'),
        'hp':    session.get('hp'),
        'attack':  base_stats.get('attack',1)  + bonus_atk,
        'defense': base_stats.get('defense',1) + bonus_def,
        'speed':   base_stats.get('speed',1)   + bonus_spd
    }

    xp_next = max(0, int(xp_threshold(player['level'] + 1) - player['xp']))

    return render_template(
        'inventory.html',
        player   = player,
        xp_to_next = xp_next,
        items    = session.get('inventory', []),
        equipped = eq
    )

@app.route('/loading')
def loading():
    return render_template('loading.html'), 202

# --- Shutdown Route ---
@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Terminate the Flask development server."""
    if func := request.environ.get('werkzeug.server.shutdown'):
        func()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
