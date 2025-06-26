from flask import Flask, render_template, request, redirect, session, url_for
import os, sys, io

# ensure Game_Modules package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game_Modules.import_assets import player_template, enemies
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
    session.clear()
    session.update({
        'player_name':    player_template.get('name', request.form['name']),
        'room_id':        player_template.get('start_room', 'R1_1'),
        'level':          player_template.get('level', 1),
        'xp':             player_template.get('xp', 0),
        'hp':             player_template.get('hp', 10),
        'potions':        player_template.get('potions', 0),
        'artifacts':      [],
        'equipped':       {'weapon': None, 'shield': None, 'armor': None},
        'bag':            [],
        'searched_rooms': [],
        'remaining':      [e['name'] for e in enemies]
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

# ----- SAVE & LOAD -----
@app.route('/save', methods=['POST'])
def save_route():
    save_load.save_game()
    return 'Game saved.', 200, {'Content-Type': 'text/plain'}

@app.route('/load', methods=['POST'])
def load_route():
    if data := save_load.load_game():
        session.update(data)
    return redirect(url_for('explore'))

# ----- EXPLORE -----
@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    # Rebuild the Player object
    player = rebuild_player(session, player_template)

    if request.method == 'POST':
        cmd = request.form['command'].strip().lower()
        action, endpoint, msg = process_explore_command(cmd, session, player_template)
        if msg:
            session['last_msg'] = msg
        if action in ('fight', 'redirect'):
            return redirect(url_for(endpoint))

    last_msg  = session.pop('last_msg', None)
    room_id   = session['room_id']
    neighbors = dungeon_map.get_neighbors(room_id)

    return render_template(
        'explore.html',
        room_name = get_room_name(room_id),
        player    = player,
        enemy     = session.get('encounter'),
        response  = last_msg,
        neighbors = neighbors,
        gear      = session['equipped'],
        artifacts = session['artifacts'],
        ROOM_NAMES=ROOM_NAMES
    )

# ----- FIGHT -----
@app.route('/fight', methods=['GET', 'POST'])
def fight():
    if 'player_name' not in session or 'encounter' not in session:
        return redirect(url_for('explore'))

    e_data = session['encounter']
    enemy  = Enemy(e_data['name'], e_data['stats'], e_data['level'])
    enemy.hp     = e_data['current_hp']
    enemy.max_hp = e_data['max_hp']

    base  = player_template.get('stats', {'attack':10, 'defense':5, 'speed':5})
    bonus = {k: sum(item.get(k,0) for item in session['equipped'].values() if item)
             for k in base}
    player = Player(
        session['player_name'],
        base['attack']  + bonus['attack'],
        base['defense'] + bonus['defense'],
        base['speed']   + bonus['speed'],
        session['level'],
        session['xp']
    )
    player.hp = session['hp']
    potions  = session['potions']
    messages = []

    if request.method == 'POST':
        action = request.form['action']
        if action == 'potion' and potions > 0:
            heal = 20
            player.hp = min(player.hp + heal, player_template.get('hp',100))
            potions -= 1
            messages.append(f"You drink a potion and recover {heal} HP.")

        if action == 'attack':
            messages.append(player_attack(player, enemy))
        elif action == 'run':
            session.pop('encounter', None)
            session.pop('enemy', None)
            session.update(hp=player.hp, potions=potions)
            session['last_msg'] = "You fled!"
            return redirect(url_for('explore'))

        if enemy.is_alive():
            messages.append(enemy_attack(player, enemy))

        session['hp']                      = max(player.hp, 0)
        session['encounter']['current_hp'] = max(enemy.hp, 0)
        session['potions']                 = potions

        if player.hp <= 0:
            return render_template('fight.html',
                                   outcome='defeat',
                                   player=player,
                                   enemy=e_data,
                                   messages=messages,
                                   potions=potions)
        if not enemy.is_alive():
            return redirect(url_for('artifact'))

        return render_template('fight.html',
                               outcome='ongoing',
                               player=player,
                               enemy=e_data,
                               messages=messages,
                               potions=potions)

    return render_template('fight.html',
                           outcome='ongoing',
                           player=player,
                           enemy=e_data,
                           messages=messages,
                           potions=potions)

# ----- ARTIFACT -----
@app.route('/artifact', methods=['GET', 'POST'])
def artifact():
    if 'encounter' not in session:
        return redirect(url_for('explore'))

    e_name = session['encounter']['name']
    puzzle = next(e['riddle'] for e in enemies if e['name'] == e_name)

    if request.method == 'POST':
        choice = int(request.form['choice'])
        if choice == puzzle['answer']:
            session['level'] += 1
            art = f"Artifact of {e_name}"
            session['artifacts'].append(art)
            session['remaining'].remove(e_name)
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['last_msg'] = f"You collected {art}!"
            if len(session['artifacts']) >= len(enemies):
                return render_template('artifact.html',
                                       final=True,
                                       question=puzzle['question'],
                                       options=puzzle['options'])
        else:
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['last_msg'] = "Wrong! The artifact vanishes."
        return redirect(url_for('explore'))

    return render_template('artifact.html',
                           final=False,
                           question=puzzle['question'],
                           options=puzzle['options'])

# ----- INVENTORY -----
@app.route('/inventory', methods=['GET', 'POST'])
def inventory_route():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        idx    = int(request.form['item_index'])
        action = request.form['action']
        if action == 'equip' and 0 <= idx < len(session['bag']): 
            it = session['bag'][idx]
            session['equipped'][it['type']] = it
        elif action == 'unequip':
            slot = request.form['slot']
            session['equipped'][slot] = None
        session.modified = True
        return redirect(url_for('inventory_route'))

    return render_template('inventory.html',
                           items=session['bag'],
                           equipped=session['equipped'])

if __name__ == '__main__':
    app.run(debug=True)
