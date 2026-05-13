class Pet:
    def __init__(self, name="Knight"):
        self.name = name
        self.hunger = 10       # 0 = starving, 10 = full
        self.happiness = 10    # 0 = sad, 10 = happy
        self.health = 10       # 0 = dead, 10 = healthy
        self.age = 0
        self.alive = True

    def tick(self):
        if not self.alive:
            return

        self.age += 1
        self.hunger = max(0, self.hunger - 1)
        self.happiness = max(0, self.happiness - 1)

        # health drops if hunger or happiness hit zero
        if self.hunger == 0 or self.happiness == 0:
            self.health = max(0, self.health - 1)

        if self.health == 0:
            self.alive = False

    def feed(self):
        if self.alive:
            self.hunger = min(10, self.hunger + 3)

    def play(self):
        if self.alive:
            self.happiness = min(10, self.happiness + 3)

    def status(self):
        return {
            "name": self.name,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "health": self.health,
            "age": self.age,
            "alive": self.alive
        }