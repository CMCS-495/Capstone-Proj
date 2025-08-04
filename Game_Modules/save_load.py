import os, json, zipfile
from io import BytesIO
from . import export_assets, import_assets, temp_utils

BASE_DIR = os.path.dirname(__file__)
SAVE_ROOT = os.path.join(BASE_DIR, 'Player_Saves')

def save_game():
    export_assets.export_assets()

def load_game():
    save_paths = []
    for player_dir in sorted(os.listdir(SAVE_ROOT)):
        dir_path = os.path.join(SAVE_ROOT, player_dir)
        if os.path.isdir(dir_path):
            save_paths.extend(
                os.path.join(dir_path, fname)
                for fname in sorted(os.listdir(dir_path))
                if fname.endswith('.json')
            )
    if not save_paths:
        print("No saves found.")
        return None
    for idx, path in enumerate(save_paths, 1):
        print(f"{idx}. {path}")
    choice = int(input("Select save to load: "))
    filepath = save_paths[choice - 1]
    with open(filepath) as f:
        data = json.load(f)
    print(f"Loaded save: {filepath}")
    return data

def load_map_from_file(path=None):
    """
    Loads the map from a JSON file.
    If no path is given, loads from the default location in Game_Assets.
    """
    if path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, 'Game_Assets', 'map.json')
    with open(path, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    print("1) Save Game")
    print("2) Load Game")
    choice = input("Choose an option: ")
    if choice == '1':
        save_game()
    elif choice == '2':
        loaded_data = load_game()
    else:
        print("Invalid option.")


def load_game_from_zip(stream, session):
    """
    stream: file-like of a .zip (e.g. request.files['save_file'].stream)
    session: the Flask session dict to populate
    """
    # 1) Open the ZIP in memory
    #    (BytesIO wrap is harmless if it's already file-like)
    buf = BytesIO(stream.read())
    with zipfile.ZipFile(buf, 'r') as z:
        import_game_data(z, session)
    # Clear out any in-combat state so you re-enter explore
    session.pop('encounter', None)
    session.pop('last_msg', None)
    session.modified = True


# TODO Rename this here and in `load_game_from_zip`
def import_game_data(z, session):
    # 2) player.json → session
    player_data = json.loads(z.read('player.json').decode('utf-8'))
    import_assets.player_template.clear()
    import_assets.player_template.update(player_data)
    stats = player_data.get('stats', {})
    session['player_name']      = player_data.get('name', '')
    session['room_id']          = player_data.get('current_map_location', '')
    session['level']            = player_data.get('level', 1)
    session['xp']               = player_data.get('xp', 0)
    session['hp']               = player_data.get('hp', stats.get('current_health',10))
    session['equipped']         = player_data.get('equipped') or player_data.get('Equipped', {})
    session['attack']           = stats.get('attack', 0)
    session['defense']          = stats.get('defense', 0)
    session['speed']            = stats.get('speed', 0)
    session['rooms_cleared']    = player_data.get('rooms_cleared', [])

    # 3) inventory.json → session
    inv = json.loads(z.read('inventory.json').decode('utf-8'))
    session['inventory']        = inv

    # 4) map.json → import_assets.game_map
    map_list = json.loads(z.read('map.json').decode('utf-8'))
    # if your rooms use 'room_id' instead of 'id', adjust accordingly
    import_assets.game_map.clear()
    import_assets.game_map.update({ r['room_id']: r for r in map_list })

    # 5) gear.json → import_assets.gear
    gear_data = json.loads(z.read('gear.json').decode('utf-8'))
    import_assets.gear.clear()
    import_assets.gear.update(gear_data)

    # 6) enemies.json → import_assets.enemies
    enemies_data = json.loads(z.read('enemies.json').decode('utf-8'))
    import_assets.enemies.clear()
    import_assets.enemies.extend(enemies_data)

    # 7) settings.json → session and import_assets
    try:
        settings_data = json.loads(z.read('settings.json').decode('utf-8'))
    except KeyError:
        settings_data = {}
    session['settings'] = settings_data
    import_assets.settings.clear()
    import_assets.settings.update(settings_data)

    for info in z.infolist():
        if info.filename.startswith('voice/'):
            tgt = os.path.join(temp_utils.VOICE_DIR, os.path.basename(info.filename))
            with open(tgt, 'wb') as f:
                f.write(z.read(info.filename))
        if info.filename.startswith('map/'):
            tgt = os.path.join(temp_utils.MAP_DIR, os.path.basename(info.filename))
            with open(tgt, 'wb') as f:
                f.write(z.read(info.filename))
