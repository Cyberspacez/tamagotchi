import os
import threading
import requests
import pygame
from pet import Pet
from save import save_pet, load_pet
from display import USE_PI, init_display

init_display()

if USE_PI:
    WIDTH, HEIGHT = 320, 240
else:
    WIDTH, HEIGHT = 400, 300

FPS = 10
FRAME_DELAY = 3
TICK_EVERY = 50

SPRITE_SCALE = 4
FRAME_COUNT = 4
FRAME_WIDTH = 16
FRAME_HEIGHT = 24

SERVER = "http://localhost:5000"

def load_frames(path, frame_count, frame_width, frame_height):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(frame_count):
        frame = sheet.subsurface(
            (i * frame_width, 0, frame_width, frame_height)
        )
        frame = pygame.transform.scale(
            frame,
            (frame_width * SPRITE_SCALE, frame_height * SPRITE_SCALE)
        )
        frames.append(frame)
    return frames

def draw_bar(screen, x, y, value, max_value, color, width=80, height=8):
    pygame.draw.rect(screen, (80, 80, 80), (x, y, width, height))
    fill = int((value / max_value) * width)
    if fill > 0:
        pygame.draw.rect(screen, color, (x, y, fill, height))

def draw_stats(screen, pet, font):
    label = font.render("H", True, (50, 50, 50))
    screen.blit(label, (10, 10))
    draw_bar(screen, 25, 12, pet.hunger, 10, (220, 80, 80))

    label = font.render("J", True, (50, 50, 50))
    screen.blit(label, (10, 26))
    draw_bar(screen, 25, 28, pet.happiness, 10, (220, 200, 80))

    label = font.render("L", True, (50, 50, 50))
    screen.blit(label, (10, 42))
    draw_bar(screen, 25, 44, pet.health, 10, (80, 180, 80))

    if pet.sleeping:
        zzz = font.render("zzz...", True, (100, 100, 180))
        screen.blit(zzz, (10, 60))
    else:
        hint = font.render("F=feed P=play S=sleep", True, (50, 80, 50))
        screen.blit(hint, (10, HEIGHT - 20))

def get_animation(pet, animations):
    if not pet.alive:
        return animations["die"]
    if pet.sleeping:
        return animations["stand"]
    if pet.health < 3:
        return animations["hurt"]
    if pet.health < 6:
        return animations["stand"]
    return animations["idle"]

def push_state(pet):
    try:
        requests.post(f"{SERVER}/push", json=pet.status(), timeout=1)
    except:
        pass

def check_outside():
    try:
        r = requests.get(f"{SERVER}/is_outside", timeout=1)
        return r.json().get("outside", False)
    except:
        return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tamagotchi")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 10)

    animations = {
        "idle":  load_frames("sprites/idle.png",  FRAME_COUNT, FRAME_WIDTH, FRAME_HEIGHT),
        "stand": load_frames("sprites/stand.png", FRAME_COUNT, FRAME_WIDTH, FRAME_HEIGHT),
        "hurt":  load_frames("sprites/hurt.png",  FRAME_COUNT, FRAME_WIDTH, FRAME_HEIGHT),
        "die":   load_frames("sprites/die.png",   FRAME_COUNT, FRAME_WIDTH, FRAME_HEIGHT),
    }

    pet = Pet("Knight")
    load_pet(pet)

    current_frame = 0
    tick = 0
    pet_tick = 0
    server_tick = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if not pet.sleeping:
                    if event.key == pygame.K_f:
                        pet.feed()
                    if event.key == pygame.K_p:
                        pet.play()
                if event.key == pygame.K_s:
                    pet.toggle_sleep()

        tick += 1
        if tick >= FRAME_DELAY:
            tick = 0
            current_frame = (current_frame + 1) % FRAME_COUNT

        pet_tick += 1
        if pet_tick >= TICK_EVERY:
            pet_tick = 0
            pet.tick()

        # push state to server every 30 ticks
        server_tick += 1
        if server_tick >= 30:
            server_tick = 0
            push_state(pet)

        # check if knight is outside
        outside = check_outside()

        if outside:
            screen.fill((30, 30, 30))
            msg = font.render("Your knight is outside...", True, (200, 200, 200))
            screen.blit(msg, (WIDTH // 2 - 80, HEIGHT // 2))
        else:
            if pet.sleeping:
                screen.fill((80, 100, 80))
            else:
                screen.fill((184, 224, 160))

            draw_stats(screen, pet, font)

            frames = get_animation(pet, animations)
            sprite_width = FRAME_WIDTH * SPRITE_SCALE
            sprite_height = FRAME_HEIGHT * SPRITE_SCALE
            x = WIDTH // 2 - sprite_width // 2
            y = HEIGHT // 2 - sprite_height // 2
            screen.blit(frames[current_frame], (x, y))

            if not pet.alive:
                dead_text = font.render("Your knight has died!", True, (180, 0, 0))
                screen.blit(dead_text, (WIDTH // 2 - 50, HEIGHT // 2))

        pygame.display.flip()
        clock.tick(FPS)

    save_pet(pet)
    pygame.quit()

if __name__ == "__main__":
    main()