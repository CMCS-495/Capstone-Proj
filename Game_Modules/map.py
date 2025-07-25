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
        self._orig_neighbors = {rid: list(r.get('neighbors', []))
                                for rid, r in self.rooms.items()}

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
        """Randomly disable rooms while keeping the map connected."""
        for rid, r in self.rooms.items():
            r.pop('disabled', None)
            r['neighbors'] = list(self._orig_neighbors.get(rid, []))

        if start_room is None:
            start_room = next(iter(self.rooms))

        def reachable(start):
            seen = {start}
            stack = [start]
            while stack:
                cur = stack.pop()
                for nbr in self.rooms.get(cur, {}).get('neighbors', []):
                    if self.rooms.get(nbr, {}).get('disabled'):
                        continue
                    if nbr not in seen:
                        seen.add(nbr)
                        stack.append(nbr)
            return seen

        others = [r for r in self.rooms if r != start_room]
        random.shuffle(others)
        for rid in others:
            if random.random() < pct:
                self.rooms[rid]['disabled'] = True
                if len(reachable(start_room)) != len(
                    [k for k, v in self.rooms.items() if not v.get('disabled')]
                ):
                    self.rooms[rid].pop('disabled', None)

        for room in self.rooms.values():
            room['neighbors'] = [n for n in room.get('neighbors', [])
                                 if not self.rooms.get(n, {}).get('disabled')]

        # Ensure the starting room has at least one available neighbour
        if not self.get_neighbors(start_room):
            choices = [n for n in self._orig_neighbors.get(start_room, [])]
            if choices:
                chosen = random.choice(choices)
                self.rooms[chosen].pop('disabled', None)
                for room in self.rooms.values():
                    room['neighbors'] = [n for n in room.get('neighbors', [])
                                         if not self.rooms.get(n, {}).get('disabled')]
