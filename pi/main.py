import os, time, sys
import requests
import pygame

SERVER_URL = os.environ.get("TAMAGOTCHI_SERVER_URL", "http://localhost:5000")

# --- GPIO (Pi only) ---
try:
    from gpiozero import Button
    BTN_FEED  = Button(17, pull_up=True, bounce_time=0.05)
    BTN_PLAY  = Button(22, pull_up=True, bounce_time=0.05)
    BTN_SLEEP = Button(27, pull_up=True, bounce_time=0.05)
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False

# --- sprite config ---
SPRITE_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "sprites")
FRAME_W  = 16
FRAME_H  = 24
SCALE    = 6
KW = FRAME_W * SCALE
KH = FRAME_H * SCALE

ANIM_FRAMES = { "idle": 4, "run": 4, "jump": 6, "hurt": 4, "die": 4, "attack": 5 }
ANIM_FILES  = { "idle": "idle.png", "stand": "stand.png", "hurt": "hurt.png", "die": "die.png" }

def load_sprites():
    sheets = {}
    for name, fname in ANIM_FILES.items():
        path = os.path.join(SPRITE_DIR, fname)
        if not os.path.exists(path):
            print(f"missing sprite: {path}")
            continue
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        count = ANIM_FRAMES.get(name, 4)
        fw = sheet.get_width() // count
        fh = sheet.get_height()
        for i in range(count):
            frame = sheet.subsurface((i * fw, 0, fw, fh))
            frame = pygame.transform.scale(frame, (KW, KH))
            frames.append(frame)
        sheets[name] = frames
    return sheets

def pick_anim(state):
    if state["health"] <= 0:      return "die"
    if state["health"] < 25:      return "hurt"
    if state["tiredness"] > 80:   return "stand"
    return "idle"

# --- server ---
def push(state):
    try:
        requests.post(f"{SERVER_URL}/api/public/push", json=state, timeout=1)
    except:
        pass

def get_outside():
    try:
        r = requests.get(f"{SERVER_URL}/api/public/is_outside", timeout=1).json()
        return bool(r.get("outside")), int(r.get("food_pending", 0))
    except:
        return False, 0

def consume_food():
    try:
        requests.post(f"{SERVER_URL}/api/public/consume_food", timeout=1)
    except:
        pass

# --- stat actions ---
def feed(state):
    state["hunger"]    = min(100, state["hunger"] + 25)
    state["animation"] = "idle"

def play(state):
    state["happiness"] = min(100, state["happiness"] + 20)
    state["tiredness"] = min(100, state["tiredness"] + 10)
    state["animation"] = "idle"

def sleep_action(state):
    state["tiredness"] = max(0, state["tiredness"] - 40)
    state["health"]    = min(100, state["health"] + 5)
    state["animation"] = "stand"

def draw_bar(screen, x, y, value, color, label, font):
    pygame.draw.rect(screen, (0, 0, 0), (x, y, 104, 10))
    pygame.draw.rect(screen, color, (x + 1, y + 1, int(value), 8))
    screen.blit(font.render(label, True, (155, 188, 15)), (x - 16, y - 1))

def main():
    pygame.init()
    screen = pygame.display.set_mode((320, 240))
    pygame.display.set_caption("Knight Tamagotchi")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("monospace", 12)
    big    = pygame.font.SysFont("monospace", 28)

    sprites = load_sprites()

    state = {
        "hunger": 80, "happiness": 80, "health": 100,
        "tiredness": 20, "animation": "idle",
    }

    frame_idx   = 0
    frame_timer = 0
    tick_timer  = 0
    push_timer  = 0
    poll_timer  = 0
    outside     = False
    food_pending = 0

    # GPIO button callbacks
    if HAS_GPIO:
        BTN_FEED.when_pressed  = lambda: feed(state)
        BTN_PLAY.when_pressed  = lambda: play(state)
        BTN_SLEEP.when_pressed = lambda: sleep_action(state)

    running = True
    while running:
        dt = clock.tick(30) / 1000.0  # seconds since last frame

        # --- events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:      feed(state)
                if event.key == pygame.K_p:      play(state)
                if event.key == pygame.K_s:      sleep_action(state)
                if event.key == pygame.K_ESCAPE: running = False

        # --- stat tick every 60 seconds ---
        tick_timer += dt
        if tick_timer >= 60:
            tick_timer = 0
            state["hunger"]    = max(0, state["hunger"]    - 2)
            state["happiness"] = max(0, state["happiness"] - 1)
            state["tiredness"] = min(100, state["tiredness"] + 2)
            if state["hunger"] < 20 or state["tiredness"] > 90:
                state["health"] = max(0, state["health"] - 3)
            elif state["hunger"] > 60 and state["tiredness"] < 60:
                state["health"] = min(100, state["health"] + 1)

        # --- push to server every 10s ---
        push_timer += dt
        if push_timer >= 10:
            push_timer = 0
            state["animation"] = pick_anim(state)
            push(state)

        # --- poll outside every 3s ---
        poll_timer += dt
        if poll_timer >= 3:
            poll_timer = 0
            outside, food_pending = get_outside()
            if food_pending > 0 and not outside:
                state["hunger"] = min(100, state["hunger"] + food_pending * 10)
                consume_food()

        # --- animation ---
        anim = pick_anim(state)
        frames = sprites.get(anim) or sprites.get("idle")
        frame_timer += dt
        if frames and frame_timer > 0.15:
            frame_timer = 0
            frame_idx = (frame_idx + 1) % len(frames)

        # --- draw ---
        screen.fill((15, 56, 15))

        if outside:
            txt = big.render("KNIGHT IS", True, (155, 188, 15))
            screen.blit(txt, txt.get_rect(center=(160, 100)))
            txt2 = big.render("OUTSIDE", True, (155, 188, 15))
            screen.blit(txt2, txt2.get_rect(center=(160, 130)))
        else:
            # draw sprite centered
            if frames:
                surf = frames[frame_idx % len(frames)]
                screen.blit(surf, surf.get_rect(center=(160, 110)))

            # draw bars
            draw_bar(screen,  36,  8, state["hunger"],    (220, 100, 60),  "H", font)
            draw_bar(screen,  36, 24, state["happiness"], (240, 220, 80),  "J", font)
            draw_bar(screen,  36, 40, state["health"],    (80,  220, 100), "L", font)
            draw_bar(screen,  36, 56, state["tiredness"], (120, 120, 200), "Z", font)

            # controls hint
            hint = font.render("F=feed P=play S=sleep", True, (100, 140, 100))
            screen.blit(hint, (10, 220))

            if state["health"] <= 0:
                txt = big.render("GAME OVER", True, (200, 50, 50))
                screen.blit(txt, txt.get_rect(center=(160, 120)))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()