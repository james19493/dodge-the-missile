# pyright: reportUndefinedVariable=false

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
import sqlite3 as sql
import pygame # type: ignore
from pygame.locals import * # type: ignore
import random
from math import cos, sin # For drawing polygons with triginometry
import os
DEBUG = False

db = "highscores.db"

os.environ['SDL_VIDEO_CENTERED'] = '1'

if pygame.init()[1]:
    pygame.quit()
    warnings.warn("There was a problem initilising the pygame library.", ImportWarning)
pygame.font.init()
pygame.mixer.init()
# To speed up or slow down the countdown sound, uncomment the following lines.
# Make sure you have the 'pyrubberband' library installed.
# Also, install 'soundfile' and 'pydub' libraries if you haven't already.
"""
from pydub import AudioSegment
import pyrubberband as pyrb
import soundfile as sf

countdown = AudioSegment.from_ogg("sounds/countdown.wav")
countdown, sr = sf.read("sounds/countdown.wav")

speed = 0.9 ### Speed factor (1.0 is normal speed, < 1.0 is slower, > 1.0 is faster) ###

stretched_countdown = pyrb.time_stretch(countdown, sr, 1.0 / speed)

sf.write("sounds/countdown.wav", stretched_countdown, sr, format='wav')"""

pygame.mixer.music.set_volume(0.5)
info = pygame.display.Info() 
WIDTH, HEIGHT = info.current_w, info.current_h

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
def get_scaled_font(size_ratio):
    return pygame.font.SysFont("Comic Sans", int(HEIGHT * size_ratio), bold=True)
# Direction key helpers
def left_pressed(keys):
    return keys[K_LEFT] or keys[K_a]

def right_pressed(keys):
    return keys[K_RIGHT] or keys[K_d]

def up_pressed(keys):
    return keys[K_UP] or keys[K_w]

def down_pressed(keys):
    return keys[K_DOWN] or keys[K_s]
# init
difficulties = ["Easy", "Medium", "Hard"]
selected = 0
player_size = 100
player_pos = [WIDTH // 2, HEIGHT // 2] # Centered player position
player_speed = 5
player_trails = [] # [x, y, sprite, age, max_age]
missiles = []
trails = [] # [x, y, dx, dy, age, max_age]
explosions = []
difficulty = "easy"
pygame.display.set_caption("Select Difficulty")
# Difficulty settings
difficulty_settings = {
    'easy':   {'player_speed': 5, 'missile_speed': 4, 'missile_spawn_rate': 95},
    'medium': {'player_speed': 4, 'missile_speed': 5, 'missile_spawn_rate': 60},
    'hard':   {'player_speed': 4, 'missile_speed': 4, 'missile_spawn_rate': 30},
}
def error():
    raise ImportError("Pygame image support is not available. Please install pygame with image support.")

LOADABLE = True if pygame.image.get_extended() else False

rocket = pygame.image.load("static/rocket.png").convert_alpha() if LOADABLE else None
rocketdown = pygame.image.load("static/rocketdown.png").convert_alpha() if LOADABLE else None
rocketup = pygame.image.load("static/rocketup.png").convert_alpha() if LOADABLE else None
rocketleft = pygame.image.load("static/rocketleft.png").convert_alpha() if LOADABLE else None
rocketright = pygame.image.load("static/rocketright.png").convert_alpha() if LOADABLE else None

if not rocket or not rocketdown or not rocketup or not rocketleft or not rocketright:
    error()

rocket = pygame.transform.scale(rocket, (100, 100))
rocketup = pygame.transform.scale(rocketup, (100, 100))
rocketdown = pygame.transform.scale(rocketdown, (100, 100))
rocketleft = pygame.transform.scale(rocketleft, (100, 100))
rocketright = pygame.transform.scale(rocketright, (100, 100))

def setup():
    global score, score_ticker, player_pos, missiles # globals
    player_pos[0] = WIDTH // 2 # centre x
    player_pos[1] = HEIGHT // 2 # centre y
    missiles.clear() # clear lists
    trails.clear() # clear lists
    player_trails.clear() # clear lists
    score = 0
    # score ticker for waiting. if score_ticker != 0, score_ticker -= 1
    # else score += 1
    # since fps = 60
    # every 60 frames the score += 1 so it is one score per second.
    score_ticker = 60
def show_instructions():
    SCREEN.fill((30, 30, 30))
    title_font = get_scaled_font(0.08)
    instruction_font = get_scaled_font(0.06)
    instruction_font2 = get_scaled_font(0.05)
    instruction_font3 = get_scaled_font(0.04)
    title_text = title_font.render("Instructions", True, (255, 255, 0))
    instruction_text = instruction_font.render("Use arrow keys or WASD to move the player.", True, (255, 255, 255))
    instruction_text2 = instruction_font2.render("Avoid the missiles that spawn from the edges!", True, (255, 255, 255))
    instruction_text3 = instruction_font3.render("Press 'H' to view highscores.", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.12)))
    instruction_rect = instruction_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.25)))
    instruction_rect2 = instruction_text2.get_rect(center=(WIDTH//2, int(HEIGHT*0.35)))
    instruction_rect3 = instruction_text3.get_rect(center=(WIDTH//2, int(HEIGHT*0.45)))
    SCREEN.blit(title_text, title_rect)
    SCREEN.blit(instruction_text, instruction_rect)
    SCREEN.blit(instruction_text2, instruction_rect2)
    SCREEN.blit(instruction_text3, instruction_rect3)
    
    back_text = instruction_font.render("Press any key to return", True, (100, 138, 200))
    back_rect = back_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.85)))
    SCREEN.blit(back_text, back_rect)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYUP:
                waiting = False
def draw_menu(current_button_colour, button_rect):
    SCREEN.fill((30, 30, 30))

    title_size = get_scaled_font(0.04)
    option_size = get_scaled_font(0.06)
    instruction_size = get_scaled_font(0.08)

    title_text = title_size.render("Select Difficulty", True, (255, 255, 255))
    instruction_text = instruction_size.render("Dodge the missiles!", True, (100, 138, 200))
    title_rect = title_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.12)))
    instruction_rect = instruction_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.25)))
    SCREEN.blit(title_text, title_rect)
    SCREEN.blit(instruction_text, instruction_rect)

    for i, diff in enumerate(difficulties):
        colour = (255, 255, 255)
        if i == selected:
            colour = (0, 255, 0)  # Highlight selected difficulty
        text = option_size.render(diff, True, colour)
        rect = text.get_rect(center=(WIDTH//2, int(HEIGHT*0.46) + i*int(HEIGHT*0.09)))
        SCREEN.blit(text, rect)

    pygame.draw.rect(SCREEN, current_button_colour, button_rect)
    text_font = get_scaled_font(0.04)
    text_surface = text_font.render("Instructions", True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=button_rect.center)
    SCREEN.blit(text_surface, text_rect)

    pygame.display.flip()

# Difficulty selection loop
def select_difficulty(first):
    SCREEN.fill((30, 30, 30))
    global selected, difficulty, settings

    normal_colour = (30, 30, 30)
    hover_colour = (40, 40, 40)
    button_rect = pygame.Rect(50, 25, 250, 50)
    current_button_colour = normal_colour

    selecting = True
    event = None
    while selecting:
        draw_menu(current_button_colour, button_rect)
        current_button_colour = normal_colour  # Reset to normal colour

        for event in pygame.event.get():
            if event.type == QUIT:
                if not first:
                    print()
                    print(f"Game Over! Score: {score}")
                    print()
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if up_pressed(keys):
                    selected = (selected - 1) % len(difficulties)
                if down_pressed(keys):
                    selected = (selected + 1) % len(difficulties)
                if event.key == K_RETURN or right_pressed(keys):
                    difficulty = difficulties[selected].lower()
                    settings = difficulty_settings[difficulty]
                    selecting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    show_instructions() 
            elif event.type == pygame.KEYUP and event.key == K_h:
                show_highscores(difficulties[selected].lower())
                SCREEN.fill((30, 30, 30))
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0] == 0:
                current_button_colour = hover_colour
            else:
                current_button_colour = normal_colour
# Setup for the main game
pygame.display.set_caption("Dodge")
clock = pygame.time.Clock()

missile_size = 10
missile_colour = (255, 0, 0)  # Red
exploding_missile_colour = (255, 165, 0)  # Orange for exploding missiles
homing_missile_colour = (252, 243, 71)  # Yellow for homing missiles

highscores = []
score = 0
score_ticker = 60

font_score = pygame.font.SysFont(None, 30)
def show_highscores(difficulty):
    SCREEN.fill((30, 30, 30))
    title_font = get_scaled_font(0.08)
    difficulty_font = get_scaled_font(0.065)
    score_font = get_scaled_font(0.06)
    title_text = title_font.render("Highscores", True, (255, 255, 0))
    difficulty_text = difficulty_font.render(difficulty.capitalize(), True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.12)))
    difficulty_rect = difficulty_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.20)))
    SCREEN.blit(title_text, title_rect)
    SCREEN.blit(difficulty_text, difficulty_rect)

    scores = get_highscores(difficulties[selected].lower(), limit=5)
    if scores:
        for i, (s, name) in enumerate(scores):
            score_text = score_font.render(f"{i+1}: {s}      {name}", True, (255, 255, 255))
            score_rect = score_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.3) + i*int(HEIGHT*0.08)))
            SCREEN.blit(score_text, score_rect)
    else:
        no_score_text = score_font.render("No scores yet!", True, (200, 200, 200))
        no_score_rect = no_score_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.30)))
        SCREEN.blit(no_score_text, no_score_rect)
    instruction_font = get_scaled_font(0.04)
    instruction_text = instruction_font.render("Press any key to return", True, (100, 138, 200))
    instruction_rect = instruction_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.85)))
    SCREEN.blit(instruction_text, instruction_rect)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYUP:
                waiting = False

def save_highscore(difficulty, score):
    # Save highscores to the database
    if not os.path.exists(db):
        conn = sql.connect(db)
        c = conn.cursor()
        c.execute("""CREATE TABLE highscores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            name TEXT NOT NULL
        )""")
        conn.commit()
        conn.close()
    
    name = prompt_name()
    conn = sql.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO highscores (difficulty, score, name) VALUES (?, ?, ?)", (difficulty.lower(), score, name))
    conn.commit()
    conn.close()
    return

def get_highscores(difficulty, limit=5):
    conn = sql.connect(db)
    c = conn.cursor()
    c.execute("SELECT score, name FROM highscores WHERE difficulty = ? ORDER BY score DESC LIMIT ?", (difficulty.lower(), limit))
    scores = c.fetchall()
    conn.close()
    return scores

def display_score():
    print()
    print(f"Game Over! Score: {score}")
    print(f"Difficulty: {difficulty.capitalize()}")

    if DEBUG:
        print("Debug Info:")
        print(f"Width: {WIDTH}, Height: {HEIGHT}")
        print(f"Player Position: {player_pos}")
        print(f"Missiles: {len(missiles)}")
    
    print()
    scores = get_highscores(difficulty.lower(), 1)
    if not scores or score > scores[0][0]:
        print(f"New High Score: {score} on {difficulty.lower()} difficulty!")
        print()
        save_highscore(difficulty.lower(), score)

    pygame.mixer.music.stop()  # Stop sound effects
    pygame.mixer.music.unload()  # Unload the music to free resources
    return

def prompt_name():
    name = ""
    font = get_scaled_font(0.06)
    instruction_font = get_scaled_font(0.04)
    active = True
    while active:
        SCREEN.fill((30, 30, 30))
        prompt_text = font.render("New High Score! Enter your name:", True, (255, 255, 0))
        name_text = font.render(name, True, (255, 255, 255))
        instruction_text = instruction_font.render("Press Enter to confirm", True, (100, 138, 200))
        SCREEN.blit(prompt_text, prompt_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.3))))
        SCREEN.blit(name_text, name_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.5))))
        SCREEN.blit(instruction_text, instruction_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.7))))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    if name:
                        active = False
                elif event.key == K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode and len(name) < 12:
                    character = event.unicode
                    if character.isprintable() and character not in ('\r', '\t', ' '):
                        name += event.unicode
    return name 
# Adapted from https://stackoverflow.com/a/57638991
# and https://stackoverflow.com/a/29064375
def draw_ngon(Surface, colour, n, radius, position, angle=0, width=2):
    pi = 3.1415926535897932384626
    x, y = position
    pygame.draw.polygon(Surface, colour, [
        (x + radius * cos(angle + (pi * 2) * i / n), y + radius * sin(angle + (pi * 2) * i / n))
        for i in range(n)
    ], width)
def draw_rocking_missile(surface, missile, time_to_explode, max_rock_time=60):
    pi = 3.1415926535897932384626

    t = max(0, min(1, (max_rock_time - time_to_explode) / max_rock_time))
    max_angle = 5  # radians

    # Oscillate angle with sine wave, frequency increases as t approaches 1
    rocking_angle = max_angle * sin(t * pi * 10)

    draw_ngon(
        surface,
        missile['colour'],
        missile['n'],
        missile['radius'],
        missile['position'],
        angle=rocking_angle,
        width=2
    )
def draw_player(keys):
    if up_pressed(keys):
        SCREEN.blit(rocketup, (player_pos[0], player_pos[1]))
    elif down_pressed(keys):
        SCREEN.blit(rocketdown, (player_pos[0], player_pos[1]))
    elif left_pressed(keys):
        SCREEN.blit(rocketleft, (player_pos[0], player_pos[1]))
    elif right_pressed(keys):
        SCREEN.blit(rocketright, (player_pos[0], player_pos[1]))
    else:
        SCREEN.blit(rocket, (player_pos[0], player_pos[1]))

def draw_player_trails():
    to_remove = []

    for t in player_trails:
        t[3] += 1
        x, y, sprite, age, max_age = t
    
        if age >= max_age:
            to_remove.append(t)
            continue

        alpha = 255 - int((age / max_age) * 255)
        if alpha < 0:
            alpha = 0

        # Create trail sprite with alpha
        trail = sprite.copy()  # Use the stored sprite from when it was created
        trail.set_alpha(alpha)
        SCREEN.blit(trail, (x - player_size // 2, y - player_size // 2))

    for t in to_remove:
        player_trails.remove(t)
def trigger_explosion(x, y):
    # Also trigger trails for damage
    num_trails = 9
    speed = 6
    for i in range(num_trails):
        angle = i * (2 * 3.14159 / num_trails)
        dx = speed * cos(angle)
        dy = speed * sin(angle)
        trails.append([x, y, dx, dy, 0, 90])  # x, y, dx, dy, age, max_age

    # Add explosion animation
    explosions.append([x, y, 10, 50, 3])  # x, y, current_radius, max_radius, growth_rate

def draw_explosions():
    to_remove = []
    for e in explosions:
        x, y, radius, max_radius, growth = e
        fade_strength = 0.6  # 0.5 to 0.8
        alpha = max(0, 255 - int((radius / max_radius) ** fade_strength * 255))

        colour = (255, 165, 0, alpha)  # orange with fading alpha

        # Since pygame doesn't support alpha with draw.circle directly,
        # Create a surface for the explosion circle with alpha
        surf = pygame.Surface((max_radius*2, max_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, colour, (max_radius, max_radius), int(radius))
        SCREEN.blit(surf, (x - max_radius, y - max_radius))

        e[2] += growth
        if e[2] >= max_radius:
            to_remove.append(e)

    for e in to_remove:
        if e in explosions:
            explosions.remove(e)

def draw_trails():
    to_remove = []
    for t in trails:
        x, y, dx, dy, age, max_age = t
        pygame.draw.circle(SCREEN, (255, 165, 0), (int(x), int(y)), 5)
        t[0] += dx
        t[1] += dy
        t[4] += 1
        if t[4] >= max_age:
            to_remove.append(t)

    for t in to_remove:
        if t in trails:
            trails.remove(t)
def draw_missiles():
    for m in missiles:
        if m[5] == "normal":
            draw_ngon(SCREEN, missile_colour, 5, missile_size, m[:2], m[3])
        elif m[5] == "exploding":
            draw_ngon(SCREEN, exploding_missile_colour, 5, missile_size + 3, m[:2], m[3], width=0)
        else:
            draw_ngon(SCREEN, homing_missile_colour, 5, missile_size + 3, m[:2], m[3], width=3)

def move_missiles():
    global score
    to_remove = []
    for m in missiles:
        m[3] += 0.125  # rotation
        direction = m[2]
        speed = m[4]

        if m[5] != "homing":
            if direction == "down":
                m[1] += speed
                if m[1] > HEIGHT:
                    to_remove.append(m)
            elif direction == "up":
                m[1] -= speed
                if m[1] < 0:
                    to_remove.append(m)
            elif direction == "right":
                m[0] += speed
                if m[0] > WIDTH:
                    to_remove.append(m)
            elif direction == "left":
                m[0] -= speed
                if m[0] < 0:
                    to_remove.append(m)

            # Exploding missile behavior
            if m[5] == "exploding":
                explode_at = m[6]

                # Distance from explosion point
                distance = None
                if m[2] == "down":
                    distance = explode_at - m[1]
                elif m[2] == "up":
                    distance = m[1] - explode_at
                elif m[2] == "right":
                    distance = explode_at - m[0]
                elif m[2] == "left":
                    distance = m[0] - explode_at

                if distance <= 50:
                    flash_color = (255, 0, 0)
                    draw_rocking_missile(SCREEN, {
                        'colour': flash_color,
                        'n': 5,
                        'radius': missile_size + 3,
                        'position': (m[0], m[1]),
                        'angle': m[3]
                        }, 
                        m[6], max_rock_time=120) 

                # Trigger explosion if the missile reaches the explode_at position
                # and remove it from the list
                if (
                    (m[2] == "down" and m[1] >= explode_at) or
                    (m[2] == "up" and m[1] <= explode_at) or
                    (m[2] == "right" and m[0] >= explode_at) or
                    (m[2] == "left" and m[0] <= explode_at)
                ):
                    trigger_explosion(m[0], m[1])
                    to_remove.append(m)
        else: # if homing missile
            # move toward the player
            dx = player_pos[0] - m[0]
            dy = player_pos[1] - m[1]

            # x and y distance are two sides of triangle, distance is hypotenuse
            distance = (dx**2 + dy**2) ** 0.5 #pythagoreas theorm. and (x^0.5) = sqrt(x)

            #x movement and y movement
            xmov = (dx / distance) * speed
            ymov = (dy / distance) * speed

            m[0] += xmov
            m[1] += ymov

    for m in to_remove:
        if m in missiles:
            missiles.remove(m)

def spawn_missiles(direction):
    if random.randint(1, settings['missile_spawn_rate']) != 1:
        return

    missile_type = "exploding" if random.randint(1, settings['missile_spawn_rate'] // 3) == 1 else "normal"
    speed = random.randint(settings['missile_speed'] - 1, settings['missile_speed'] + 1)

    if missile_type == "exploding":
        if random.randint(1, (settings['missile_spawn_rate'] // 2)) == 1: missile_type = "homing"
    
    explode_at = None
    if missile_type == "exploding":
        explode_at = random.randint(50, HEIGHT - 50) if direction in ("up", "down") else random.randint(50, WIDTH - 50)

    # Missile start position (x, y)
    if direction in ("up", "down"):
        x_pos = player_pos[0] if random.randint(1, round(settings['missile_spawn_rate'] / 1.5)) == 1 else random.randint(missile_size, WIDTH - missile_size)
        y_pos = 0 if direction == "down" else HEIGHT
    elif direction in ("left", "right"):
        y_pos = player_pos[1] if random.randint(1, round(settings['missile_spawn_rate'] / 1.5)) == 1 else random.randint(missile_size, HEIGHT - missile_size)
        x_pos = WIDTH if direction == "left" else 0
    else:
        return  # Invalid direction

    missiles.append([x_pos, y_pos, direction, 0, speed, missile_type, explode_at])
def check_collision():
    player_rect = pygame.Rect(*player_pos, player_size - 20, player_size - 15)

    # Determine current player sprite based on keys (same logic as draw_player)
    keys = pygame.key.get_pressed()
    if up_pressed(keys):
        player_sprite = rocketup
    elif down_pressed(keys):
        player_sprite = rocketdown
    elif left_pressed(keys):
        player_sprite = rocketleft
    elif right_pressed(keys):
        player_sprite = rocketright
    else:
        player_sprite = rocket

    # Create player mask once
    player_mask = pygame.mask.from_surface(player_sprite)
    player_topleft = (int(player_pos[0]), int(player_pos[1]))

    # Check missiles with rect early-out, then pixel-perfect mask overlap
    for m in missiles:
        missile_rect = pygame.Rect(int(m[0] - missile_size), int(m[1] - missile_size), missile_size*2, missile_size*2)
        if not player_rect.colliderect(missile_rect):
            continue

        # Prepare a temporary surface for the missile polygon as drawn on screen
        radius = missile_size + 3 if m[5] != "normal" else missile_size
        surf_size = int(radius * 2 + 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

        cx = surf_size // 2
        cy = surf_size // 2

        # Draw the missile on temp surface using same appearance as draw_missiles
        colour = exploding_missile_colour if m[5] != "normal" else missile_colour
        width = 0 if m[5] != "normal" else 2
        # draw_ngon expects (Surface, colour, n, radius, position, angle=0, width=2)
        draw_ngon(surf, colour, 5, radius, (cx, cy), angle=m[3], width=width)

        missile_mask = pygame.mask.from_surface(surf)

        # Compute top-left of missile surf on screen (draw_ngon used center)
        missile_topleft = (int(m[0] - cx), int(m[1] - cy))

        offset = (missile_topleft[0] - player_topleft[0], missile_topleft[1] - player_topleft[1])

        if player_mask.overlap(missile_mask, offset):
            return True

    # Check trails (small circles) with same approach
    for t in trails:
        trail_rect = pygame.Rect(int(t[0] - 5), int(t[1] - 5), 10, 10)
        if not player_rect.colliderect(trail_rect):
            continue

        r = 5
        surf_size = r * 2 + 4
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 165, 0, 255), (surf_size//2, surf_size//2), r)

        trail_mask = pygame.mask.from_surface(surf)
        trail_topleft = (int(t[0] - surf_size//2), int(t[1] - surf_size//2))
        offset = (trail_topleft[0] - player_topleft[0], trail_topleft[1] - player_topleft[1])

        if player_mask.overlap(trail_mask, offset):
            return True

    return False
def cool_animation():
    clock = pygame.time.Clock()
    SCREEN.fill((30, 30, 30))

    pygame.mixer.music.stop()  # Stop sound effects
    pygame.mixer.music.unload()  # Unload the music to free resources
    pygame.mixer.music.load("sounds/countdown.wav")

    arrow_font = get_scaled_font(1.3)
    arrow_text = arrow_font.render("\u00BB", True, (255, 255, 255))

    spawn_x = 0
    arrows = [spawn_x]
    total_arrows_spawned = 1
    max_arrows = 3

    group_speed = 800
    acceleration = 800

    # Trail setup
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Time tracking
    spawn_interval = 0.8  # seconds between each arrow
    time_since_last_spawn = 0

    pygame.mixer.music.play()  # Sound effects

    exit = False
    running = True
    while running:
        dt = clock.tick(144) / 1000.0  # delta time in seconds
        time_since_last_spawn += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
                running = False

        # Update group speed with easing logic
        if arrows:
            lead_pos = arrows[-1]
            if lead_pos < WIDTH // 2:
                group_speed += acceleration * dt
            else:
                group_speed -= acceleration * dt
        group_speed = max(group_speed, 50)

        # Update positions
        arrows = [x + group_speed * dt for x in arrows]

        # Spawn new arrow at fixed time intervals
        if total_arrows_spawned < max_arrows and time_since_last_spawn >= spawn_interval:
            arrows.append(spawn_x)
            total_arrows_spawned += 1
            time_since_last_spawn = 0

        # Fade trail
        trail_surface.fill((0, 0, 0, 25))
        SCREEN.blit(trail_surface, (0, 0))

        # Draw arrows
        for pos in arrows:
            title_rect = arrow_text.get_rect(center=(pos, int(HEIGHT * 0.3)))
            SCREEN.blit(arrow_text, title_rect)

        pygame.display.flip()

        # Exit condition
        if total_arrows_spawned == max_arrows and arrows[-1] - round(WIDTH*0.48394495412844036) > WIDTH: # Caluculations by https://www.wolframalpha.com/input?i=400%2F1744+as+a+fraction
            running = False
    
    pygame.mixer.music.stop()  # Stop sound effects
    return exit

def play():
    if cool_animation():
        display_score()
        pygame.quit()
        exit()

    pygame.mixer.music.stop()  # Stop sound effects
    pygame.mixer.music.unload()  # Unload the music to free resources
    pygame.mixer.music.load("sounds/background.wav")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # Loop the countdown sound
    pygame.mixer.music.set_pos(0)  # Reset position to the start

    pygame.time.delay(200)

    global run
    global score
    global score_ticker
    global difficulty, settings, selected

    
    # Main game loop
    while run:
        pygame.event.pump()
        score_ticker -= 1
        if (score_ticker == 0):
            score += 1
            score_ticker = 60

        clock.tick(60)
        SCREEN.fill((30, 30, 30))
        for event in pygame.event.get():
            if event.type == QUIT:
                display_score()
                run = False
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if event.key == K_ESCAPE:
                    pygame.display.iconify()

        keys = pygame.key.get_pressed()
        if left_pressed(keys) and player_pos[0] > 0:
            player_pos[0] -= player_speed
        if right_pressed(keys) and player_pos[0] < WIDTH - player_size:
            player_pos[0] += player_speed
        if up_pressed(keys) and player_pos[1] > 0:
            player_pos[1] -= player_speed
        if down_pressed(keys) and player_pos[1] < HEIGHT - player_size:
            player_pos[1] += player_speed

        

        # Determine which sprite is active right now
        if up_pressed(keys):
            current_sprite = rocketup
        elif down_pressed(keys):
            current_sprite = rocketdown
        elif left_pressed(keys):
            current_sprite = rocketleft
        elif right_pressed(keys):
            current_sprite = rocketright
        else:
            current_sprite = rocket

        # Store the sprite and center position
        player_trails.append([
            player_pos[0] + player_size // 2,  # center x
            player_pos[1] + player_size // 2,  # center y
            current_sprite,                    # sprite image
            0,                                 # age
            4,                                 # max_age
        ])
 

        for direction in ["up", "down", "left", "right"]:
           spawn_missiles(direction)


        draw_player(keys)
        draw_player_trails()

        move_missiles()
        draw_missiles()

        draw_trails() # And move them
        draw_explosions()
     

        if check_collision():
            pygame.mixer.music.stop()

            scores = get_highscores(difficulty, 1)
            
            if not scores or score > scores[0][0]:
                save_highscore(difficulty, score)
            again = gameover_menu()
            
            if again == True:
                setup()
                play()
        
            elif again == "change":
                select_difficulty(False)
                setup()
                play()
                 

            display_score()
            run = False
   

        score_text = font_score.render(f"Score: {score}", True, (255, 255, 255))
        SCREEN.blit(score_text, (10, 10))

        pygame.display.flip()

        

    pygame.mixer.music.unload()
    pygame.quit()
    exit()

def draw_gameover(selected_option):
    ############# Draw Game Over SCREEN #############

    SCREEN.fill((30, 30, 30))
    title_font = get_scaled_font(0.09)
    option_font = get_scaled_font(0.06)
    score_font = get_scaled_font(0.05)

    over_text = title_font.render("Game Over!", True, (255, 0, 0))
    score_text = score_font.render(f"Score: {score}", True, (255, 255, 255))
    over_rect = over_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.15)))
    score_rect = score_text.get_rect(center=(WIDTH//2, int(HEIGHT*0.25)))
    SCREEN.blit(over_text, over_rect)
    SCREEN.blit(score_text, score_rect)

    options = ["Replay", "Change Difficulty", "Quit"]
    for i, opt in enumerate(options):
        for event in pygame.event.get():
            if event.type == QUIT:
                display_score()
                pygame.quit()
                exit()
        colour = (255, 255, 255)
        if i == selected_option:
            colour = (0, 255, 0)
        text = option_font.render(opt, True, colour)
        rect = text.get_rect(center=(WIDTH//2, int(HEIGHT*0.50) + i*int(HEIGHT*0.09)))
        SCREEN.blit(text, rect)
    pygame.display.flip()

def gameover_menu():
    SCREEN.fill((30, 30, 30))

    selected_option = None
    draw_gameover(selected_option)
    pygame.event.clear() # Clear all pending events
    pygame.time.wait(1) # Short delay to avoid instant selection
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                display_score()
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if event.key == K_ESCAPE:
                    pygame.display.iconify()

                if selected_option is None:
                    if up_pressed(keys):
                        selected_option = 0
                    elif down_pressed(keys):
                        selected_option = 1
                else:
                    if up_pressed(keys):
                        selected_option = (selected_option - 1) % 3
                    elif down_pressed(keys):
                        selected_option = (selected_option + 1) % 3
                    elif event.key == K_RETURN or right_pressed(keys):
                        if selected_option is None:
                            selected_option = 0
                        elif selected_option == 0:
                            return True  # Replay
                        elif selected_option == 1:
                            return "change"  # Change difficulty
                        elif selected_option == 2:
                            return False # Quit
            elif event.type == pygame.KEYUP and event.key == K_h:
                show_highscores(difficulty)
                
        draw_gameover(selected_option)

##### MAIN FUNCTION #####
def main():
    global run, score, score_ticker, difficulty, settings, selected
    select_difficulty(True)
    setup()
    pygame.display.set_caption("Dodge the missiles!")
    run = True
    play() 

if __name__ == "__main__":
    main()
    pygame.quit()
    exit()

# HELLO THERE! YOU HAVE REACHED THE END OF THIS FILE!

