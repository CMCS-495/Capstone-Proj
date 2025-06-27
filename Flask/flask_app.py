from flask import (
    Flask, render_template, request,
    redirect, session, url_for, send_file, flash
)
import os, sys, io, time, zipfile, json

# ensure Game_Modules package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game_Modules.import_assets import inventory, gear, game_map, enemies, player_template
from Game_Modules import llm_client
from Game_Modules.save_load   import save_game
from Game_Modules import save_load
from Game_Modules.export_assets import SAVE_ROOT
from Game_Modules.entities import Player, Enemy
from Game_Modules.combat import player_attack, enemy_attack
from Game_Modules.game_utils import (
    rebuild_player,
    get_room_name,
    process_explore_command,
    dungeon_map
)
from Game_Modules import rng, save_load

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Precompute ROOM_NAMES mapping for templates
ROOM_NAMES = {rid: get_room_name(rid) for rid in dungeon_map.rooms.keys()}

# ----- MAIN MENU -----
@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/start', methods=['POST'])
def start_game():
    # Clear any old session
    session.clear()

    # Grab the name the user entered; if they submitted nothing, fall back to the template default
    player_name = request.form.get('name', '').strip()
    if not player_name:
        player_name = player_template.get('name', 'Adventurer')

    session.update({
        'player_name': player_name,
        'room_id':      player_template.get('start_room', 'R1_1'),
        'level':        player_template.get('level', 1),
        'xp':           player_template.get('xp', 0),
        'hp':           player_template.get('hp', 10),
        'equipped':     {
            'weapon': None, 'shield': None, 'armor': None,
            'boots':  None, 'ring':   None, 'helmet': None
        },
        'inventory':    []
    })
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

@app.route('/load_save', methods=['GET', 'POST'])
def load_save():
    # Display form on GET, process upload on POST
    if request.method == 'POST':
        file = request.files.get('save_file')
        if file and file.filename.endswith('.zip'):
            # Clear out any existing session state
            session.clear()
            # load_game_from_zip should unpack into session
            try:
                save_load.load_game_from_zip(file.stream, session)
                flash("Save loaded successfully.", "success")
                return redirect(url_for('explore'))
            except Exception as e:
                flash(f"Failed to load save: {e}", "error")
        else:
            flash("Please upload a valid .zip save file.", "error")
    return render_template('load_save.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Simple stub: store e.g. "difficulty" in session
    if request.method == 'POST':
        diff = request.form.get('difficulty')
        session['settings'] = session.get('settings', {})
        session['settings']['difficulty'] = diff
        flash(f"Difficulty set to {diff}", "success")
        return redirect(url_for('menu'))
    # On GET, show the form
    current = session.get('settings', {}).get('difficulty', 'Normal')
    return render_template('settings.html', current=current)

# ----- EXPLORE -----
@app.route('/explore', methods=['GET','POST'])
def explore():
    # 1) Ensure in-game
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    # 2) Handle any POSTed command
    if request.method == 'POST':
        cmd = request.form.get('command','').strip().lower()
        action, endpoint, msg = process_explore_command(cmd, session, player_template)
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
    player = Player(
        session['player_name'],
        base.get('attack',1)  + bonus['attack'],
        base.get('defense',1) + bonus['defense'],
        base.get('speed',1)   + bonus['speed'],
        session.get('level',1),
        session.get('xp',0)
    )
    player.hp = session.get('hp', player.hp)

    # 4) Lazy-generate room description
    room_id = session['room_id']
    room    = game_map[room_id]
    if not room.get('llm_description'):
        ctx = {'prompt':room.get('llm_prompt',''),
               'neighbors':room.get('neighbors',[])}
        room['llm_description'] = llm_client.generate_description('room', ctx)

    # 5) Build neighbor list & names map
    neighbors = dungeon_map.get_neighbors(room_id)
    ROOM_NAMES = {rid: r.get('name',rid) for rid,r in game_map.items()}

    # 6) Pull a one-time message and potion count
    response = session.pop('last_msg','')
    potions  = len([i for i in session.get('inventory',[]) if i.get('type')=='aid'])

    # 7) Render with **xp** and **player.name** guaranteed in context
    return render_template('explore.html',
        player_name      = session['player_name'],
        player           = player,
        xp               = session.get('xp', 0),
        room_name        = room.get('name', room_id),
        room_description = room['llm_description'],
        gear             = eq,
        artifacts        = session.get('artifacts', []),
        neighbors        = neighbors,
        enemy            = session.get('encounter'),
        response         = response,
        potions          = potions,
        ROOM_NAMES       = ROOM_NAMES
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
    player = Player(
        session['player_name'],
        base['attack']  + bonus['attack'],
        base['defense'] + bonus['defense'],
        base['speed']   + bonus['speed'],
        session['level'],
        session['xp']
    )
    player.hp = session['hp']

    # Count aid items in inventory as "potions"
    inv = session.setdefault('inventory', [])
    aid_items = [i for i in inv if i.get('type') == 'aid']
    potions = len(aid_items)

    messages = []

    if request.method == 'POST':
        action = request.form['action']

        # Drink an aid item if available
        if action == 'potion' and potions > 0:
            heal_amount = 20
            # consume one aid item
            for idx, itm in enumerate(inv):
                if itm.get('type') == 'aid':
                    inv.pop(idx)
                    break
            potions -= 1

            player.hp = min(player.hp + heal_amount, player_template.get('stats',{}).get('max_health',100))
            messages.append(f"You use an aid item and recover {heal_amount} HP.")

        if action == 'attack':
            messages.append(player_attack(player, enemy))
        elif action == 'run':
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['hp'] = player.hp
            session['inventory'] = inv
            session['last_msg'] = "You fled!"
            return redirect(url_for('explore'))

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

    # Fetch the enemy’s encounter rate (0–100)
    enc_rate = e_data.get('encounter_rate', 0)
    if enc_rate > 0:
        # Rarer enemies (low rate) give more XP
        xp_gain = int(100 / enc_rate)
    else:
        # Fallback for malformed data
        xp_gain = 1

    # Award XP
    session['xp'] = session.get('xp', 0) + xp_gain

    # Let the player know
    session['last_msg'] = f"You gained {xp_gain} XP!"

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
            if action == 'equip':
                eq[slot] = item
            else:  # unequip
                eq[slot] = None

        # Use aid items
        elif action == 'use' and 0 <= idx < len(inv):
            if inv[idx].get('type') == 'aid':
                inv.pop(idx)

        # Drop gear
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

    return render_template(
        'inventory.html',
        player   = player,
        items    = session.get('inventory', []),
        equipped = eq
    )

@app.route('/loading')
def loading():
    return render_template('loading.html'), 202

if __name__ == '__main__':
    app.run(debug=True)
