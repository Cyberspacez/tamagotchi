import os

# Set this to True when running on the Raspberry Pi
USE_PI = False

def init_display():
    if USE_PI:
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        os.environ["SDL_VIDEODRIVER"] = "fbcon"