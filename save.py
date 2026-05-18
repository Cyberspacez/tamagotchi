import json
import os

SAVE_FILE = "save.json"

def save_pet(pet):
    data = {
        "name": pet.name,
        "hunger": pet.hunger,
        "happiness": pet.happiness,
        "health": pet.health,
        "age": pet.age,
        "alive": pet.alive
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_pet(pet):
    if not os.path.exists(SAVE_FILE):
        return  # no save file yet, use defaults
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
    pet.name = data["name"]
    pet.hunger = data["hunger"]
    pet.happiness = data["happiness"]
    pet.health = data["health"]
    pet.age = data["age"]
    pet.alive = data["alive"]