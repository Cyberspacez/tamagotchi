class Pet:
    def __init__(self, name="Knight"):
        self.name = name
        self.hunger = 10
        self.happiness = 10
        self.health = 10
        self.age = 0
        self.alive = True
        self.sleeping = False
        self.tiredness = 0      # 0 = awake, 10 = exhausted

    def tick(self):
        if not self.alive:
            return

        self.age += 1

        if self.sleeping:
            # recover while sleeping
            self.tiredness = max(0, self.tiredness - 3)
            self.hunger = max(0, self.hunger - 1)  # still gets hungry
            if self.tiredness == 0:
                self.sleeping = False  # wake up automatically
        else:
            self.hunger = max(0, self.hunger - 1)
            self.happiness = max(0, self.happiness - 1)
            self.tiredness = min(10, self.tiredness + 1)

        if self.hunger == 0 or self.happiness == 0:
            self.health = max(0, self.health - 1)

        if self.health == 0:
            self.alive = False

    def feed(self):
        if self.alive and not self.sleeping:
            self.hunger = min(10, self.hunger + 3)

    def play(self):
        if self.alive and not self.sleeping:
            self.happiness = min(10, self.happiness + 3)
            self.tiredness = min(10, self.tiredness + 1)

    def toggle_sleep(self):
        if self.alive:
            self.sleeping = not self.sleeping

    def status(self):
        return {
            "name": self.name,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "health": self.health,
            "age": self.age,
            "alive": self.alive,
            "sleeping": self.sleeping,
            "tiredness": self.tiredness
        }