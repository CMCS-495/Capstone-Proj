import random

def get_llm_response(prompt):
    p = prompt.lower()
    # Enemy generation if prompt mentions enemy
    if "enemy" in p and "found" not in p:
        enemies = [
            {"name": "Shadow Beast", "description": "A creature formed from smoke and nightmare.",
             "stats": {"attack": 5, "defense": 3, "speed": 2}, "level": 1},
            {"name": "Venom Imp",    "description": "A tiny demon with venomous claws and a screeching laugh.",
             "stats": {"attack": 7, "defense": 4, "speed": 4}, "level": 2},
            {"name": "Bone Knight",  "description": "An armored skeleton warrior wielding a cursed sword.",
             "stats": {"attack": 9, "defense": 6, "speed": 3}, "level": 3},
            {"name": "Flame Wraith", "description": "A ghost wrapped in fire, gliding above the ground.",
             "stats": {"attack": 10, "defense": 5, "speed": 6}, "level": 4},
            {"name": "Dreadlord",    "description": "A towering presence of evil with eyes that pierce souls.",
             "stats": {"attack": 12, "defense": 8, "speed": 5}, "level": 5},
        ]
        return random.choice(enemies)

    # Gear generation if prompt explicitly about finding gear
    if "you found a gear item" in p:
        gear = [
            {"name": "Iron Sword",     "type": "weapon", "attack": 3, "defense": 0, "speed": 0},
            {"name": "Leather Armor",  "type": "armor",  "attack": 0, "defense": 2, "speed": 0},
            {"name": "Swift Boots",    "type": "boots",  "attack": 0, "defense": 0, "speed": 2},
            {"name": "Steel Helmet",   "type": "helmet", "attack": 0, "defense": 3, "speed": 0},
            {"name": "Ring of Fury",   "type": "ring",   "attack": 2, "defense": 1, "speed": 1},
        ]
        return random.choice(gear)

    # Default room descriptions
    descriptions = [
        "The air is thick with magic. Strange runes glow faintly on the walls.",
        "Torches crackle as shadows dance along moss-covered stone.",
        "Chains hang from the ceiling. Something just moved in the dark.",
        "A pool of glowing liquid bubbles at the center of the room.",
        "Skeletal remains lie in a circle. One hand clutches a scroll.",
        "A whispering breeze carries unintelligible voices around you."
    ]
    return random.choice(descriptions)
