class DungeonMap:
    def __init__(self, map_data):
        # map_data is a list of room dicts
        self.rooms = {room["id"]: room for room in map_data}

    def is_valid_move(self, current_room, target_room):
        return target_room in self.rooms.get(current_room, {}).get("neighbors", [])

    def get_neighbors(self, room_id):
        return self.rooms.get(room_id, {}).get("neighbors", [])
