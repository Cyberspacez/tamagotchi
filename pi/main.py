"""
Raspberry Pi tamagotchi client.
Set SERVER_URL to your PC's local IP, e.g. http://192.168.1.50:5000
If you run this on the same PC as the server, http://localhost:5000 works.
"""
import os, time, json, sys
import requests

SERVER_URL = os.environ.get("TAMAGOTCHI_SERVER_URL", "http://localhost:5000")

# --- Try pygame for display, gpiozero for buttons. Both optional. ---
try:
    import pygame
    HAS_PYGAME = True
except Exception:
    HAS_PYGAME = False

try:
    from gpiozero import Button
    BTN_FEED = Button(17)
    BTN_PLAY = Button(22)
    BTN_SLEEP = Button(27)
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False
    BTN_FEED = BTN_PLAY = BTN_SLEEP = None

state = {
    "hunger": 50, "happiness": 50, "health": 100, "tiredness": 30,
    "animation": "idle",
}

def push():
    try:
        requests.post(f"{SERVER_URL}/api/public/push", json=state, timeout=2)
    except Exception as e:
        print("push fail:", e)

def is_outside():
    try:
        r = requests.get(f"{SERVER_URL}/api/public/is_outside", timeout=2).json()
        return bool(r.get("outside")), int(r.get("food_pending", 0))
    except Exception:
        return False, 0

def consume_pending_food():
    try:
        requests.post(f"{SERVER_URL}/api/public/consume_food", timeout=2)
    except Exception:
        pass

def tick():
    state["hunger"] = min(100, state["hunger"] + 0.5)
    state["happiness"] = max(0, state["happiness"] - 0.3)
    state["tiredness"] = min(100, state["tiredness"] + 0.4)
    if state["hunger"] > 80 or state["tiredness"] > 90:
        state["health"] = max(0, state["health"] - 0.2)

def feed():
    state["hunger"] = max(0, state["hunger"] - 25)
    state["animation"] = "eat"

def play():
    state["happiness"] = min(100, state["happiness"] + 20)
    state["tiredness"] = min(100, state["tiredness"] + 10)
    state["animation"] = "happy"

def sleep_action():
    state["tiredness"] = max(0, state["tiredness"] - 40)
    state["animation"] = "sleep"

def main():
    print(f"Connecting to {SERVER_URL}")
    if HAS_PYGAME:
        pygame.init()
        screen = pygame.display.set_mode((320, 240))
        pygame.display.set_caption("Knight Tamagotchi")
        font = pygame.font.SysFont("monospace", 14)
        big = pygame.font.SysFont("monospace", 40)
    last_push = 0
    running = True
    while running:
        if HAS_PYGAME:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f: feed()
                    if event.key == pygame.K_p: play()
                    if event.key == pygame.K_s: sleep_action()
        if HAS_GPIO:
            if BTN_FEED.is_pressed: feed()
            if BTN_PLAY.is_pressed: play()
            if BTN_SLEEP.is_pressed: sleep_action()

        tick()
        outside, pending = is_outside()
        if pending > 0 and not outside:
            consume_pending_food()
            state["hunger"] = max(0, state["hunger"] - pending * 10)

        if time.time() - last_push > 2:
            push(); last_push = time.time()

        if HAS_PYGAME:
            screen.fill((15, 56, 15))
            if outside:
                screen.blit(big.render("OUTSIDE", True, (155,188,15)), (60, 90))
            else:
                screen.blit(big.render("KNIGHT", True, (155,188,15)), (70, 20))
                y = 90
                for k in ["hunger","happiness","health","tiredness"]:
                    screen.blit(font.render(f"{k}: {int(state[k])}", True, (155,188,15)), (20, y))
                    y += 24
            pygame.display.flip()
        time.sleep(0.1)

if HAS_PYGAME: pygame.quit()

if __name__ == "__main__":
    main()
