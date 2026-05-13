import pygame

# Window settings
SCALE = 4
SPRITE_SCALE = 8
WIDTH, HEIGHT = 128 * SCALE, 64 * SCALE

# Animation settings
FPS = 10
FRAME_DELAY = 3

# Sprite settings
FRAME_COUNT = 4
FRAME_WIDTH = 16
FRAME_HEIGHT = 24

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

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tamagotchi")
    clock = pygame.time.Clock()

    frames = load_frames(
        "sprites/idle.png",
        FRAME_COUNT,
        FRAME_WIDTH,
        FRAME_HEIGHT
    )

    current_frame = 0
    tick = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        tick += 1
        if tick >= FRAME_DELAY:
            tick = 0
            current_frame = (current_frame + 1) % len(frames)

        screen.fill((184, 224, 160))

        sprite_width = FRAME_WIDTH * SPRITE_SCALE
        sprite_height = FRAME_HEIGHT * SPRITE_SCALE
        x = WIDTH // 2 - sprite_width // 2
        y = HEIGHT // 2 - sprite_height // 2

        screen.blit(frames[current_frame], (x, y))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()