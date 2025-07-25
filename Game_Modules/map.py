import random


class DungeonMap:
    def __init__(self, map_data):
        """
        Initialize the dungeon map.

        Accepts either:
          - a list of room dicts (from map.json), using 'id' or 'room_id' as key, or
          - a dict mapping room IDs to room dicts.
        """
        # Normalize list-of-rooms into dict keyed by room ID
        if isinstance(map_data, dict):
            # already keyed by room ID
            self.rooms = map_data
        else:
            rooms = {}
            for room in map_data:
                if key := room.get('id') or room.get('room_id'):
                    rooms[key] = room
            self.rooms = rooms

    def is_valid_move(self, current_room, target_room):
        """Return True if ``target_room`` is a valid enabled neighbour."""
        if self.rooms.get(target_room, {}).get('disabled'):
            return False
        neighbors = self.rooms.get(current_room, {}).get('neighbors', [])
        return target_room in neighbors

    def get_neighbors(self, room_id):
        """
        Return a list of neighbor room IDs for `room_id`, or an empty list.
        """
        return list(self.rooms.get(room_id, {}).get('neighbors', []))

    def randomize_rooms(self, start_room=None, pct=0.3):
        """Randomly disable rooms except ``start_room`` and cleanup neighbors."""
        for r in self.rooms.values():
            r.pop('disabled', None)

        if start_room is None:
            start_room = next(iter(self.rooms))

        for rid, room in self.rooms.items():
            if rid == start_room:
                continue
            if random.random() < pct:
                room['disabled'] = True

        for room in self.rooms.values():
            room['neighbors'] = [n for n in room.get('neighbors', [])
                                 if not self.rooms.get(n, {}).get('disabled')]
