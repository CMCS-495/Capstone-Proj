class Player:
    def __init__(self, name, attack=0, defense=0, speed=0, level=1, xp=0):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.level = level
        self.xp = xp
        self.hp = 100

    def take_damage(self, amt):
        self.hp = max(0, self.hp - amt)

    def is_alive(self):
        return self.hp > 0

class Enemy:
    def __init__(self, name, stats, level=1):
        self.name = name
        self.level = level
        self.attack = stats.get("attack", 0)
        self.defense = stats.get("defense", 0)
        self.speed = stats.get("speed", 0)
        self.hp = 50 + (level * 10)

    def take_damage(self, amt):
        self.hp = max(0, self.hp - amt)

    def is_alive(self):
        return self.hp > 0
