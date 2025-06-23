# flask_app.py

from flask import (
    Flask, render_template, request,
    redirect, session, url_for
)
import random, os

from Game_Modules.llm_client import get_llm_response
from Game_Modules.entities  import Player, Enemy
from Game_Modules.save_load import load_map_from_file
from Game_Modules.map       import DungeonMap

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Load & Name Rooms ---
map_data    = load_map_from_file()      # flat list of room dicts
dungeon_map = DungeonMap(map_data)

ROOM_NAMES = {
    "R1_1": "Twilight Hollow",
    "R1_2": "Ashen Vault",
    "R1_3": "Echoing Crypt",
    "R1_4": "Serpent's Pit",
    "R1_5": "Sanctum of Shadows"
}

# --- Gear Pool (3 types) ---
GEAR_POOL = [
    {"name":"Iron Sword",     "type":"weapon","attack":10,"defense":0,"speed":0},
    {"name":"Bronze Shield",  "type":"shield","attack":0,"defense":3,"speed":0},
    {"name":"Chainmail Armor","type":"armor", "attack":0,"defense":5,"speed":-1},
]

# --- Enemy Definitions & Riddles (5 total) ---
ENEMIES = [
    {
      "name":"Shadow Beast",
      "description":"A creature formed from smoke and nightmare.",
      "stats":{"attack":5,"defense":3,"speed":2},
      "level":1,
      "riddle":{
        "question":"I am always hungry, I must always be fed, but if you give me water I die. What am I?",
        "options":["A flame","A shadow","A beast"],
        "answer":0
      }
    },
    {
      "name":"Venom Imp",
      "description":"A screeching imp with venomous claws.",
      "stats":{"attack":7,"defense":4,"speed":4},
      "level":2,
      "riddle":{
        "question":"I speak without a mouth and hear without ears. I have nobody, but I come alive with wind. What am I?",
        "options":["An echo","A spirit","A dream"],
        "answer":0
      }
    },
    {
      "name":"Bone Knight",
      "description":"An armored skeleton warrior wielding a cursed sword.",
      "stats":{"attack":9,"defense":6,"speed":3},
      "level":3,
      "riddle":{
        "question":"What walks on four legs in the morning, two legs at noon, and three legs in the evening?",
        "options":["A dog","A human","A table"],
        "answer":1
      }
    },
    {
      "name":"Flame Wraith",
      "description":"A ghost wrapped in fire, gliding above the ground.",
      "stats":{"attack":10,"defense":5,"speed":6},
      "level":4,
      "riddle":{
        "question":"I have cities, but no houses; I have mountains, but no trees; I have water, but no fish. What am I?",
        "options":["A map","A desert","A dream"],
        "answer":0
      }
    },
    {
      "name":"Dreadlord",
      "description":"A towering presence of evil with eyes that pierce souls.",
      "stats":{"attack":12,"defense":8,"speed":5},
      "level":5,
      "riddle":{
        "question":"What can run but never walks, has a mouth but never talks, has a head but never weeps, has a bed but never sleeps?",
        "options":["A river","A clock","A shadow"],
        "answer":0
      }
    }
]

# --- Probabilities ---
ENEMY_SPAWN_CHANCE    = 0.6
SEARCH_SUCCESS_CHANCE = 0.5

# ----- MAIN MENU -----
@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/start', methods=['POST'])
def start_game():
    session.clear()
    session.update({
      'player_name':    request.form['name'],
      'room_id':        'R1_1',
      'level':          1,
      'xp':             0,
      'hp':             100,
      'potions':        2,
      'artifacts':      [],
      'equipped':       {"weapon":None,"shield":None,"armor":None},
      'bag':            [],
      'searched_rooms': [],
      'remaining':      [e['name'] for e in ENEMIES]
    })
    return redirect(url_for('explore'))

# ----- EXPLORE -----
@app.route('/explore', methods=['GET','POST'])
def explore():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    name       = session['player_name']
    room_id    = session['room_id']
    encounter  = session.get('encounter')
    last_msg   = session.pop('last_msg', None)

    # rebuild Player with gear bonuses
    base = {'attack':5,'defense':3,'speed':4}
    gear = session['equipped']
    bonus = {k: sum(item.get(k,0) for item in gear.values() if item) for k in base}
    player = Player(
        name,
        base['attack']  + bonus['attack'],
        base['defense'] + bonus['defense'],
        base['speed']   + bonus['speed'],
        session['level'],
        session['xp']
    )
    player.hp = session['hp']

    if request.method=='POST':
        cmd = request.form['command']

        # FIGHT
        if cmd=='fight' and encounter:
            return redirect(url_for('fight'))

        # RUN
        if cmd=='run':
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['last_msg'] = "You fled the fight!"
            return redirect(url_for('explore'))

        # MOVE
        if cmd.startswith('go '):
            _, tgt = cmd.split(None,1)
            if tgt==room_id:
                session['last_msg']="You're already here."
            elif dungeon_map.is_valid_move(room_id, tgt):
                session['room_id'] = tgt
                session.pop('encounter', None)
                session.pop('enemy', None)
                # spawn only from remaining
                if session['remaining'] and random.random() < ENEMY_SPAWN_CHANCE:
                    name = random.choice(session['remaining'])
                    e    = next(e for e in ENEMIES if e['name']==name).copy()
                    max_hp = 15 + (e['level']-1)*5
                    e.update({'max_hp':max_hp,'current_hp':max_hp})
                    session['enemy']     = e['name']
                    session['encounter'] = e
                    session['last_msg']  = f"<b>Enemy:</b> {e['name']} — {e['description']}"
                else:
                    session['last_msg'] = f"You enter {ROOM_NAMES[tgt]}. It's quiet."
            else:
                session['last_msg']="Can't go that way."
            return redirect(url_for('explore'))

        # SEARCH
        if cmd=='search':
            if encounter:
                session['last_msg']="An enemy blocks your search!"
            else:
                sr = session['searched_rooms']
                if room_id in sr:
                    session['last_msg']="You already searched here."
                else:
                    sr.append(room_id); session['searched_rooms']=sr
                    if random.random()<SEARCH_SUCCESS_CHANCE and len(session['bag'])<3:
                        avail = [g for g in GEAR_POOL
                                 if g['type'] not in [i['type'] for i in session['bag']]]
                        if avail:
                            item = random.choice(avail)
                            session['bag'].append(item)
                            session['last_msg']=f"Found gear: {item['name']}"
                        else:
                            session['last_msg']="No more gear left."
                    else:
                        session['last_msg']="Nothing found."
            return redirect(url_for('explore'))

        # INVENTORY
        if cmd=='inventory':
            return redirect(url_for('inventory'))

        # UNKNOWN
        session['last_msg']="Unknown command."
        return redirect(url_for('explore'))

    # GET or post-redirect
    response  = last_msg or get_llm_response(f"{name} explores {ROOM_NAMES[room_id]}")
    neighbors = dungeon_map.get_neighbors(room_id)

    return render_template('explore.html',
        room_name = ROOM_NAMES[room_id],
        player    = player,
        enemy     = session.get('encounter'),
        response  = response,
        neighbors = neighbors,
        gear      = gear,
        artifacts = session['artifacts'],
        ROOM_NAMES=ROOM_NAMES
    )

# ----- FIGHT -----
@app.route('/fight', methods=['GET','POST'])
def fight():
    if 'player_name' not in session or 'encounter' not in session:
        return redirect(url_for('explore'))

    # rebuild enemy
    e     = session['encounter']
    enemy = Enemy(e['name'], e['stats'], e['level'])
    enemy.hp     = e['current_hp']
    enemy.max_hp = e['max_hp']

    # rebuild player
    base = {'attack':10,'defense':5,'speed':5}
    gear = session['equipped']
    bonus = {k: sum(item.get(k,0) for item in gear.values() if item) for k in base}
    player = Player(
        session['player_name'],
        base['attack']  + bonus['attack'],
        base['defense'] + bonus['defense'],
        base['speed']   + bonus['speed'],
        session['level'],
        session['xp']
    )
    player.hp  = session['hp']
    potions    = session['potions']
    messages   = []

    if request.method=='POST':
        action = request.form['action']
        defend = (action=='defend')

        # POTION
        if action=='potion' and potions>0:
            heal = 20
            player.hp = min(100, player.hp + heal)
            potions -= 1
            messages.append(f"You drink a potion and recover {heal} HP.")

        # ATTACK
        if action=='attack':
            dmg = max(10, player.attack - enemy.defense)
            enemy.take_damage(dmg)
            messages.append(f"You strike {enemy.name} for {dmg} damage.")

        # RUN
        if action=='run':
            session.pop('encounter', None)
            session.pop('enemy', None)
            session['hp']      = player.hp
            session['potions'] = potions
            session['last_msg']= "You fled!"
            return redirect(url_for('explore'))

        # ENEMY COUNTER
        if enemy.hp > 0:
            dmg2 = max(1, enemy.attack - player.defense)
            if defend:
                dmg2 //= 10
                messages.append("Your guard holds, halving the hit!")
            player.take_damage(dmg2)
            messages.append(f"{enemy.name} hits you for {dmg2} damage.")

        # persist stats
        session['hp']        = max(0, player.hp)
        e['current_hp']      = max(0, enemy.hp)
        session['encounter'] = e
        session['potions']   = potions

        # DEFEAT?
        if player.hp <= 0:
            return render_template('fight.html',
                outcome='defeat',
                player=player,
                enemy=e,
                messages=messages,
                potions=potions
            )

        # VICTORY → riddle
        if enemy.hp <= 0:
            return redirect(url_for('artifact'))

        # ONGOING
        return render_template('fight.html',
            outcome='ongoing',
            player=player,
            enemy=e,
            messages=messages,
            potions=potions
        )

    # initial GET
    return render_template('fight.html',
        outcome='ongoing',
        player=player,
        enemy=e,
        messages=[],
        potions=potions
    )

# ----- ARTIFACT / RIDDLE -----
@app.route('/artifact', methods=['GET','POST'])
def artifact():
    if 'encounter' not in session:
        return redirect(url_for('explore'))

    e      = session['encounter']
    puzzle = next(x['riddle'] for x in ENEMIES if x['name']==e['name'])

    if request.method=='POST':
        choice = int(request.form['choice'])
        if choice == puzzle['answer']:
            # Level up
            session['level'] += 1
            art = f"Artifact of {e['name']}"
            session['artifacts'].append(art)
            session['remaining'].remove(e['name'])
            session.pop('encounter', None)
            session.pop('enemy',     None)
            session['last_msg']=f"You collected {art}!"

            # Final victory?
            if len(session['artifacts']) >= 5:
                return render_template('artifact.html',
                    final=True,
                    question=puzzle['question'],
                    options=puzzle['options']
                )
            return redirect(url_for('explore'))
        else:
            session.pop('encounter', None)
            session.pop('enemy',     None)
            session['last_msg']="Wrong! The artifact vanishes."
            return redirect(url_for('explore'))

    return render_template('artifact.html',
        final=False,
        question=puzzle['question'],
        options=puzzle['options']
    )

# ----- INVENTORY -----
@app.route('/inventory', methods=['GET','POST'])
def inventory():
    if 'player_name' not in session:
        return redirect(url_for('menu'))

    bag      = session['bag']
    equipped = session['equipped']

    if request.method=='POST':
        act = request.form['action']
        idx = int(request.form['item_index'])
        if act=='equip' and 0<=idx<len(bag):
            it = bag[idx]
            equipped[it['type']] = it
        elif act=='unequip':
            slot = request.form['slot']
            equipped[slot] = None
        session['equipped'] = equipped
        return redirect(url_for('inventory'))

    return render_template('inventory.html',
        items    = bag,
        equipped = equipped
    )

if __name__=='__main__':
    app.run(debug=True)
