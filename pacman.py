import copy
from board import boards
import pygame
import math
import json
import os

pygame.init()

# Dostupná rozlišení (v poměru 900:950)
AVAILABLE_RESOLUTIONS = [
    (900, 950),
    (1080, 1140),
    (1260, 1330),
    (1440, 1520)
]

# Načtení nastavení
def load_settings():
    default_settings = {
        'resolution': 0,  # Index do AVAILABLE_RESOLUTIONS
        'fullscreen': False
    }
    if os.path.exists('settings.json'):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Ověřit validitu
                if 'resolution' not in settings or settings['resolution'] >= len(AVAILABLE_RESOLUTIONS):
                    settings['resolution'] = 0
                if 'fullscreen' not in settings:
                    settings['fullscreen'] = False
                return settings
        except:
            return default_settings
    return default_settings

def save_settings(settings):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def apply_settings(settings):
    global WIDTH, HEIGHT, screen
    WIDTH, HEIGHT = AVAILABLE_RESOLUTIONS[settings['resolution']]
    flags = (pygame.FULLSCREEN | pygame.SCALED) if settings['fullscreen'] else 0
    screen = pygame.display.set_mode([WIDTH, HEIGHT], flags)
    pygame.display.set_caption('PAC-MAN')

game_settings = load_settings()

WIDTH, HEIGHT = AVAILABLE_RESOLUTIONS[game_settings['resolution']]
screen = pygame.display.set_mode([WIDTH, HEIGHT], (pygame.FULLSCREEN | pygame.SCALED) if game_settings['fullscreen'] else 0)
pygame.display.set_caption('PAC-MAN')
timer = pygame.time.Clock()
fps = 60
font = pygame.font.Font('freesansbold.ttf', 20)
level = copy.deepcopy(boards)
color = 'blue'
PI = math.pi
player_images = []
for i in range(1, 5):
    player_images.append(pygame.transform.scale(pygame.image.load(f'assets/player_images/{i}.png'), (45, 45)))
blinky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/red.png'), (45, 45))
pinky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/pink.png'), (45, 45))
inky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/blue.png'), (45, 45))
clyde_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/orange.png'), (45, 45))
spooked_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/powerup.png'), (45, 45))
dead_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/dead.png'), (45, 45))
player_x = 450
player_y = 663
direction = 0
blinky_x = 56
blinky_y = 58
blinky_direction = 0
inky_x = 440
inky_y = 388
inky_direction = 2
pinky_x = 440
pinky_y = 438
pinky_direction = 2
clyde_x = 440
clyde_y = 438
clyde_direction = 2
counter = 0
flicker = False
# R - doprava, L - doleva, U - nahoru, D - dolů
turns_allowed = [False, False, False, False]
direction_command = 0
player_speed = 2
score = 0
powerup = False
power_counter = 0
eaten_ghost = [False, False, False, False]
targets = [(player_x, player_y), (player_x, player_y), (player_x, player_y), (player_x, player_y)]
blinky_dead = False
inky_dead = False
clyde_dead = False
pinky_dead = False
blinky_box = False
inky_box = False
clyde_box = False
pinky_box = False
moving = False
ghost_speeds = [2, 2, 2, 2]
startup_counter = 0
lives = 3
game_over = False
main_menu = True
show_scoreboard = False
show_settings = False
entering_name = False
player_name = ""
current_level = 1

# Načtení scoreboardu
def load_scoreboard():
    if os.path.exists('scoreboard.json'):
        with open('scoreboard.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_scoreboard(scores):
    with open('scoreboard.json', 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

def is_top_10(current_score, scores):
    if len(scores) < 10:
        return True
    return current_score > scores[-1]['score']

def get_power_duration(level_num):
    # Začíná na 600 (10 sekund), snižuje se o 30 každý level, minimum 180 (3 sekundy)
    duration = 600 - ((level_num - 1) * 30)
    return max(duration, 180)

def get_ghost_base_speed(level_num):
    # Začíná na 2, zvyšuje se o 0.1 každý level, maximum 4
    speed = 2 + ((level_num - 1) * 0.1)
    return min(speed, 4)

scoreboard = load_scoreboard()


class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id):
        self.x_pos = x_coord
        self.y_pos = y_coord
        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22
        self.target = target
        self.speed = speed
        self.img = img
        self.direction = direct
        self.dead = dead
        self.in_box = box
        self.id = id
        self.turns, self.in_box = self.check_collisions()
        self.rect = self.draw()

    def draw(self):
        if (not powerup and not self.dead) or (eaten_ghost[self.id] and powerup and not self.dead):
            screen.blit(self.img, (self.x_pos, self.y_pos))
        elif powerup and not self.dead and not eaten_ghost[self.id]:
            screen.blit(spooked_img, (self.x_pos, self.y_pos))
        else:
            screen.blit(dead_img, (self.x_pos, self.y_pos))
        ghost_rect = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36, 36))
        return ghost_rect

    def check_collisions(self):
        # R, L, U, D
        num1 = ((HEIGHT - 50) // 32)
        num2 = (WIDTH // 30)
        num3 = 15
        self.turns = [False, False, False, False]
        # Konverze na int pro správné indexování
        center_x_int = int(self.center_x)
        center_y_int = int(self.center_y)
        if 0 < center_x_int // 30 < 29:
            if level[(center_y_int - num3) // num1][center_x_int // num2] == 9:
                self.turns[2] = True
            if level[center_y_int // num1][(center_x_int - num3) // num2] < 3 \
                    or (level[center_y_int // num1][(center_x_int - num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if level[center_y_int // num1][(center_x_int + num3) // num2] < 3 \
                    or (level[center_y_int // num1][(center_x_int + num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if level[(center_y_int + num3) // num1][center_x_int // num2] < 3 \
                    or (level[(center_y_int + num3) // num1][center_x_int // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if level[(center_y_int - num3) // num1][center_x_int // num2] < 3 \
                    or (level[(center_y_int - num3) // num1][center_x_int // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= center_x_int % num2 <= 18:
                    if level[(center_y_int + num3) // num1][center_x_int // num2] < 3 \
                            or (level[(center_y_int + num3) // num1][center_x_int // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(center_y_int - num3) // num1][center_x_int // num2] < 3 \
                            or (level[(center_y_int - num3) // num1][center_x_int // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= center_y_int % num1 <= 18:
                    if level[center_y_int // num1][(center_x_int - num2) // num2] < 3 \
                            or (level[center_y_int // num1][(center_x_int - num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[center_y_int // num1][(center_x_int + num2) // num2] < 3 \
                            or (level[center_y_int // num1][(center_x_int + num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= center_x_int % num2 <= 18:
                    if level[(center_y_int + num3) // num1][center_x_int // num2] < 3 \
                            or (level[(center_y_int + num3) // num1][center_x_int // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(center_y_int - num3) // num1][center_x_int // num2] < 3 \
                            or (level[(center_y_int - num3) // num1][center_x_int // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= center_y_int % num1 <= 18:
                    if level[center_y_int // num1][(center_x_int - num3) // num2] < 3 \
                            or (level[center_y_int // num1][(center_x_int - num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[center_y_int // num1][(center_x_int + num3) // num2] < 3 \
                            or (level[center_y_int // num1][(center_x_int + num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True
        if 350 < self.x_pos < 550 and 370 < self.y_pos < 480:
            self.in_box = True
        else:
            self.in_box = False
        return self.turns, self.in_box

    def move_clyde(self):
        # r, l, u, d
        # Clyde se bude otáčet, kdykoli je to výhodné pro pronásledování
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos - 30
        return self.x_pos, self.y_pos, self.direction

    def move_blinky(self):
        # r, l, u, d
        # Blinky se bude otáčet pouze při kolizi se zdmi, jinak jede rovně
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[2]:
                self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[3]:
                self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos - 30
        return self.x_pos, self.y_pos, self.direction

    def move_inky(self):
        # r, l, u, d
        # Inky se může otáčet nahoru nebo dolů kdykoliv kvůli pronásledování, ale vlevo/vpravo jen při kolizi
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos - 30
        return self.x_pos, self.y_pos, self.direction

    def move_pinky(self):
        # r, l, u, d
        # Pinky se bude otáčet vlevo nebo vpravo, když je to výhodné, ale nahoru/dolů pouze při kolizi
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos - 30
        return self.x_pos, self.y_pos, self.direction


def draw_misc():
    score_text = font.render(f'Skóre: {score}', True, 'white')
    screen.blit(score_text, (10, 920))
    level_text = font.render(f'Level: {current_level}', True, 'white')
    screen.blit(level_text, (350, 920))
    if powerup:
        pygame.draw.circle(screen, 'blue', (140, 930), 15)
    for i in range(lives):
        screen.blit(pygame.transform.scale(player_images[0], (30, 30)), (650 + i * 40, 915))
    if game_over:
        pygame.draw.rect(screen, 'white', [50, 200, 800, 300],0, 10)
        pygame.draw.rect(screen, 'dark gray', [70, 220, 760, 260], 0, 10)
        gameover_text = font.render('Game over! Stiskni MEZERNÍK pro restart!', True, 'red')
        screen.blit(gameover_text, (100, 300))


def check_collisions(scor, power, power_count, eaten_ghosts):
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    if 0 < player_x < 870:
        if level[center_y // num1][center_x // num2] == 1:
            level[center_y // num1][center_x // num2] = 0
            scor += 10
        if level[center_y // num1][center_x // num2] == 2:
            level[center_y // num1][center_x // num2] = 0
            scor += 50
            power = True
            power_count = 0
            eaten_ghosts = [False, False, False, False]
    return scor, power, power_count, eaten_ghosts


def draw_board():
    num1 = ((HEIGHT - 50) // 32)
    num2 = (WIDTH // 30)
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            if level[i][j] == 2 and not flicker:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
            if level[i][j] == 3:
                pygame.draw.line(screen, color, (j * num2 + (0.5 * num2), i * num1),
                                 (j * num2 + (0.5 * num2), i * num1 + num1), 3)
            if level[i][j] == 4:
                pygame.draw.line(screen, color, (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            if level[i][j] == 5:
                pygame.draw.arc(screen, color, [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                0, PI / 2, 3)
            if level[i][j] == 6:
                pygame.draw.arc(screen, color,
                                [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1], PI / 2, PI, 3)
            if level[i][j] == 7:
                pygame.draw.arc(screen, color, [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1], PI,
                                3 * PI / 2, 3)
            if level[i][j] == 8:
                pygame.draw.arc(screen, color,
                                [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1], 3 * PI / 2,
                                2 * PI, 3)
            if level[i][j] == 9:
                pygame.draw.line(screen, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)


def draw_player():
    # 0 - doprava, 1 - doleva, 2 - nahoru, 3 - dolů
    if direction == 0:
        screen.blit(player_images[counter // 5], (player_x, player_y))
    elif direction == 1:
        screen.blit(pygame.transform.flip(player_images[counter // 5], True, False), (player_x, player_y))
    elif direction == 2:
        screen.blit(pygame.transform.rotate(player_images[counter // 5], 90), (player_x, player_y))
    elif direction == 3:
        screen.blit(pygame.transform.rotate(player_images[counter // 5], 270), (player_x, player_y))


def check_position(centerx, centery):
    turns = [False, False, False, False]
    num1 = (HEIGHT - 50) // 32
    num2 = (WIDTH // 30)
    num3 = 15
    # kontroluje kolize podle středu hráče (x, y) ± posun
    if centerx // 30 < 29:
        if direction == 0:
            if level[centery // num1][(centerx - num3) // num2] < 3:
                turns[1] = True
        if direction == 1:
            if level[centery // num1][(centerx + num3) // num2] < 3:
                turns[0] = True
        if direction == 2:
            if level[(centery + num3) // num1][centerx // num2] < 3:
                turns[3] = True
        if direction == 3:
            if level[(centery - num3) // num1][centerx // num2] < 3:
                turns[2] = True

        if direction == 2 or direction == 3:
            if 12 <= centerx % num2 <= 18:
                if level[(centery + num3) // num1][centerx // num2] < 3:
                    turns[3] = True
                if level[(centery - num3) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if level[centery // num1][(centerx - num2) // num2] < 3:
                    turns[1] = True
                if level[centery // num1][(centerx + num2) // num2] < 3:
                    turns[0] = True
        if direction == 0 or direction == 1:
            if 12 <= centerx % num2 <= 18:
                if level[(centery + num1) // num1][centerx // num2] < 3:
                    turns[3] = True
                if level[(centery - num1) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if level[centery // num1][(centerx - num3) // num2] < 3:
                    turns[1] = True
                if level[centery // num1][(centerx + num3) // num2] < 3:
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True

    return turns


def move_player(play_x, play_y):
    # r - vpravo, l - vlevo, u - nahoru, d - dolů
    if direction == 0 and turns_allowed[0]:
        play_x += player_speed
    elif direction == 1 and turns_allowed[1]:
        play_x -= player_speed
    if direction == 2 and turns_allowed[2]:
        play_y -= player_speed
    elif direction == 3 and turns_allowed[3]:
        play_y += player_speed
    return play_x, play_y


def draw_scoreboard():
    screen.fill('black')
    title_font = pygame.font.Font('freesansbold.ttf', 60)
    title_text = title_font.render('TOP 10', True, 'yellow')
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    
    score_font = pygame.font.Font('freesansbold.ttf', 30)
    y_pos = 150
    
    for i, entry in enumerate(scoreboard[:10]):
        rank_text = f"{i+1}. {entry['name']}: {entry['score']}"
        text_surface = score_font.render(rank_text, True, 'white')
        screen.blit(text_surface, (150, y_pos))
        y_pos += 50
    
    # Tlačítko zpět
    back_font = pygame.font.Font('freesansbold.ttf', 35)
    back_text = back_font.render('Zpět', True, 'white')
    back_rect = pygame.Rect(WIDTH // 2 - 100, 800, 200, 50)
    pygame.draw.rect(screen, 'blue', back_rect, 3)
    screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, 808))
    
    return back_rect


def draw_name_input(current_score):
    screen.fill('black')
    title_font = pygame.font.Font('freesansbold.ttf', 50)
    title_text = title_font.render('GRATULUJEME!', True, 'yellow')
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))
    
    score_font = pygame.font.Font('freesansbold.ttf', 40)
    score_text = score_font.render(f'Skóre: {current_score}', True, 'white')
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))
    
    prompt_font = pygame.font.Font('freesansbold.ttf', 30)
    prompt_text = prompt_font.render('Zadejte své jméno:', True, 'white')
    screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, 350))
    
    # Input box
    input_rect = pygame.Rect(WIDTH // 2 - 200, 420, 400, 60)
    pygame.draw.rect(screen, 'white', input_rect, 3)
    
    name_font = pygame.font.Font('freesansbold.ttf', 35)
    name_text = name_font.render(player_name, True, 'white')
    screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, 435))
    
    hint_font = pygame.font.Font('freesansbold.ttf', 25)
    hint_text = hint_font.render('Stiskněte ENTER pro potvrzení', True, 'gray')
    screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, 550))


def draw_settings():
    screen.fill('black')
    title_font = pygame.font.Font('freesansbold.ttf', 60)
    title_text = title_font.render('NASTAVEN\u00cd', True, 'yellow')
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    
    settings_font = pygame.font.Font('freesansbold.ttf', 35)
    
    # Rozlišení
    res_label = settings_font.render('Rozli\u0161en\u00ed:', True, 'white')
    screen.blit(res_label, (150, 200))
    
    resolution_rects = []
    for i, (w, h) in enumerate(AVAILABLE_RESOLUTIONS):
        y_pos = 270 + i * 70
        res_text = settings_font.render(f'{w}x{h}', True, 'white')
        res_rect = pygame.Rect(200, y_pos, 500, 50)
        
        if game_settings['resolution'] == i:
            pygame.draw.rect(screen, 'green', res_rect, 3)
            pygame.draw.circle(screen, 'green', (180, y_pos + 25), 8)
        else:
            pygame.draw.rect(screen, 'gray', res_rect, 3)
            pygame.draw.circle(screen, 'gray', (180, y_pos + 25), 8, 2)
        
        if False:  # Skryto - rozlišení není viditelné
            screen.blit(res_text, (220, y_pos + 8))
    
    # Fullscreen
    fullscreen_y = 270 + len(AVAILABLE_RESOLUTIONS) * 70 + 30
    fs_label = settings_font.render('Re\u017eim:', True, 'white')
    screen.blit(fs_label, (150, fullscreen_y))
    
    fs_rect = pygame.Rect(200, fullscreen_y + 70, 500, 50)
    fs_text = settings_font.render(
        'Fullscreen' if game_settings['fullscreen'] else 'Windowed',
        True, 'white'
    )
    
    if game_settings['fullscreen']:
        pygame.draw.rect(screen, 'green', fs_rect, 3)
    else:
        pygame.draw.rect(screen, 'blue', fs_rect, 3)
    
    screen.blit(fs_text, (WIDTH // 2 - fs_text.get_width() // 2, fullscreen_y + 78))
    
    apply_rect = pygame.Rect(WIDTH // 2 - 250, HEIGHT - 150, 200, 50)
    back_rect = pygame.Rect(WIDTH // 2 + 50, HEIGHT - 150, 200, 50)
    
    pygame.draw.rect(screen, 'green', apply_rect, 3)
    pygame.draw.rect(screen, 'red', back_rect, 3)
    
    button_font = pygame.font.Font('freesansbold.ttf', 30)
    apply_text = button_font.render('Pou\u017e\u00edt', True, 'white')
    back_text = button_font.render('Zp\u011bt', True, 'white')
    
    screen.blit(apply_text, (WIDTH // 2 - 250 + (200 - apply_text.get_width()) // 2, HEIGHT - 142))
    screen.blit(back_text, (WIDTH // 2 + 50 + (200 - back_text.get_width()) // 2, HEIGHT - 142))
    
    return resolution_rects, fs_rect, apply_rect, back_rect


def draw_menu():
    screen.fill('black')
    # Nadpis
    title_font = pygame.font.Font('freesansbold.ttf', 70)
    title_text = title_font.render('PAC-MAN', True, 'yellow')
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
    
    # Tlačítka menu
    menu_font = pygame.font.Font('freesansbold.ttf', 40)
    
    # Hrát
    play_text = menu_font.render('Hrát', True, 'white')
    play_rect = pygame.Rect(WIDTH // 2 - 150, 300, 300, 60)
    pygame.draw.rect(screen, 'blue', play_rect, 3)
    screen.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, 310))
    
    # Scoreboard
    scoreboard_text = menu_font.render('Scoreboard', True, 'white')
    scoreboard_rect = pygame.Rect(WIDTH // 2 - 150, 400, 300, 60)
    pygame.draw.rect(screen, 'green', scoreboard_rect, 3)
    screen.blit(scoreboard_text, (WIDTH // 2 - scoreboard_text.get_width() // 2, 410))
    
    # Nastaveni
    settings_text = menu_font.render('Nastaven\u00ed', True, 'white')
    settings_rect = pygame.Rect(WIDTH // 2 - 150, 500, 300, 60)
    pygame.draw.rect(screen, 'orange', settings_rect, 3)
    screen.blit(settings_text, (WIDTH // 2 - settings_text.get_width() // 2, 510))
    
    # Odejít
    quit_text = menu_font.render('Odejít', True, 'white')
    quit_rect = pygame.Rect(WIDTH // 2 - 150, 600, 300, 60)
    pygame.draw.rect(screen, 'red', quit_rect, 3)
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, 610))
    
    return play_rect, scoreboard_rect, settings_rect, quit_rect


def get_targets(blink_x, blink_y, ink_x, ink_y, pink_x, pink_y, clyd_x, clyd_y):
    if player_x < 450:
        runaway_x = 900
    else:
        runaway_x = 0
    if player_y < 450:
        runaway_y = 900
    else:
        runaway_y = 0
    return_target = (380, 400)
    if powerup:
        if not blinky.dead and not eaten_ghost[0]:
            blink_target = (runaway_x, runaway_y)
        elif not blinky.dead and eaten_ghost[0]:
            if 340 < blink_x < 560 and 340 < blink_y < 500:
                blink_target = (400, 100)
            else:
                blink_target = (player_x, player_y)
        else:
            blink_target = return_target
        if not inky.dead and not eaten_ghost[1]:
            ink_target = (runaway_x, player_y)
        elif not inky.dead and eaten_ghost[1]:
            if 340 < ink_x < 560 and 340 < ink_y < 500:
                ink_target = (400, 100)
            else:
                ink_target = (player_x, player_y)
        else:
            ink_target = return_target
        if not pinky.dead:
            pink_target = (player_x, runaway_y)
        elif not pinky.dead and eaten_ghost[2]:
            if 340 < pink_x < 560 and 340 < pink_y < 500:
                pink_target = (400, 100)
            else:
                pink_target = (player_x, player_y)
        else:
            pink_target = return_target
        if not clyde.dead and not eaten_ghost[3]:
            clyd_target = (450, 450)
        elif not clyde.dead and eaten_ghost[3]:
            if 340 < clyd_x < 560 and 340 < clyd_y < 500:
                clyd_target = (400, 100)
            else:
                clyd_target = (player_x, player_y)
        else:
            clyd_target = return_target
    else:
        if not blinky.dead:
            if 340 < blink_x < 560 and 340 < blink_y < 500:
                blink_target = (400, 100)
            else:
                blink_target = (player_x, player_y)
        else:
            blink_target = return_target
        if not inky.dead:
            if 340 < ink_x < 560 and 340 < ink_y < 500:
                ink_target = (400, 100)
            else:
                ink_target = (player_x, player_y)
        else:
            ink_target = return_target
        if not pinky.dead:
            if 340 < pink_x < 560 and 340 < pink_y < 500:
                pink_target = (400, 100)
            else:
                pink_target = (player_x, player_y)
        else:
            pink_target = return_target
        if not clyde.dead:
            if 340 < clyd_x < 560 and 340 < clyd_y < 500:
                clyd_target = (400, 100)
            else:
                clyd_target = (player_x, player_y)
        else:
            clyd_target = return_target
    return [blink_target, ink_target, pink_target, clyd_target]


run = True
while run:
    timer.tick(fps)
    
    if entering_name:
        # Zadávání jména po hře
        draw_name_input(score)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(player_name) > 0:
                    # Uložit skóre
                    scoreboard.append({'name': player_name, 'score': score})
                    scoreboard.sort(key=lambda x: x['score'], reverse=True)
                    scoreboard = scoreboard[:10]  # Ponechat pouze TOP 10
                    save_scoreboard(scoreboard)
                    player_name = ""
                    entering_name = False
                    main_menu = True
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key != pygame.K_RETURN and len(player_name) < 15:
                    # Přidat znak
                    if event.unicode.isprintable():
                        player_name += event.unicode
        
        pygame.display.flip()
        continue
    
    if show_scoreboard:
        # Zobrazit scoreboard
        back_rect = draw_scoreboard()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if back_rect.collidepoint(mouse_pos):
                    show_scoreboard = False
                    main_menu = True
        
        pygame.display.flip()
        continue
    
    if show_settings:
        # Zobrazit nastavení
        resolution_rects, fs_rect, apply_rect, back_rect = draw_settings()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Kliknutí na rozlišení - skryto
                if False:
                    for i, rect in enumerate(resolution_rects):
                        if rect.collidepoint(mouse_pos):
                            game_settings['resolution'] = i
                
                # Kliknutí na fullscreen přepínač
                if fs_rect.collidepoint(mouse_pos):
                    game_settings['fullscreen'] = not game_settings['fullscreen']
                
                # Použít nastavení
                if apply_rect.collidepoint(mouse_pos):
                    save_settings(game_settings)
                    apply_settings(game_settings)
                    show_settings = False
                    main_menu = True
                
                # Zpět bez uložení
                if back_rect.collidepoint(mouse_pos):
                    game_settings = load_settings()  # Načíst původní nastavení
                    show_settings = False
                    main_menu = True
        
        pygame.display.flip()
        continue
    
    if main_menu:
        # Zobrazit menu
        play_rect, scoreboard_rect, settings_rect, quit_rect = draw_menu()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if play_rect.collidepoint(mouse_pos):
                    # Reset hry
                    main_menu = False
                    score = 0
                    lives = 3
                    level = copy.deepcopy(boards)
                    powerup = False
                    power_counter = 0
                    player_x = 450
                    player_y = 663
                    direction = 0
                    direction_command = 0
                    blinky_x = 56
                    blinky_y = 58
                    blinky_direction = 0
                    inky_x = 440
                    inky_y = 388
                    inky_direction = 2
                    pinky_x = 440
                    pinky_y = 438
                    pinky_direction = 2
                    clyde_x = 440
                    clyde_y = 438
                    clyde_direction = 2
                    eaten_ghost = [False, False, False, False]
                    blinky_dead = False
                    inky_dead = False
                    clyde_dead = False
                    pinky_dead = False
                    game_over = False
                    startup_counter = 0
                    current_level = 1
                elif scoreboard_rect.collidepoint(mouse_pos):
                    main_menu = False
                    show_scoreboard = True
                elif settings_rect.collidepoint(mouse_pos):
                    main_menu = False
                    show_settings = True
                elif quit_rect.collidepoint(mouse_pos):
                    run = False
        
        pygame.display.flip()
        continue
    
    if counter < 19:
        counter += 1
        if counter > 3:
            flicker = False
    else:
        counter = 0
        flicker = True
    if powerup and power_counter < get_power_duration(current_level):
        power_counter += 1
    elif powerup and power_counter >= get_power_duration(current_level):
        power_counter = 0
        powerup = False
        eaten_ghost = [False, False, False, False]
    if startup_counter < 180 and not game_over:
        moving = False
        startup_counter += 1
    else:
        moving = True

    screen.fill('black')
    draw_board()
    center_x = player_x + 23
    center_y = player_y + 24
    
    # Rychlost duchů podle levelu
    base_speed = get_ghost_base_speed(current_level)
    if powerup:
        ghost_speeds = [1, 1, 1, 1]
    else:
        ghost_speeds = [base_speed, base_speed, base_speed, base_speed]
    if eaten_ghost[0]:
        ghost_speeds[0] = 2
    if eaten_ghost[1]:
        ghost_speeds[1] = 2
    if eaten_ghost[2]:
        ghost_speeds[2] = 2
    if eaten_ghost[3]:
        ghost_speeds[3] = 2
    if blinky_dead:
        ghost_speeds[0] = 4
    if inky_dead:
        ghost_speeds[1] = 4
    if pinky_dead:
        ghost_speeds[2] = 4
    if clyde_dead:
        ghost_speeds[3] = 4

    level_complete = True
    for i in range(len(level)):
        if 1 in level[i] or 2 in level[i]:
            level_complete = False
    
    # Pokud je level dokončen, restart s vyšší obtížností
    if level_complete:
        current_level += 1
        level = copy.deepcopy(boards)
        powerup = False
        power_counter = 0
        player_x = 450
        player_y = 663
        direction = 0
        direction_command = 0
        blinky_x = 56
        blinky_y = 58
        blinky_direction = 0
        inky_x = 440
        inky_y = 388
        inky_direction = 2
        pinky_x = 440
        pinky_y = 438
        pinky_direction = 2
        clyde_x = 440
        clyde_y = 438
        clyde_direction = 2
        eaten_ghost = [False, False, False, False]
        blinky_dead = False
        inky_dead = False
        clyde_dead = False
        pinky_dead = False
        startup_counter = 0

    player_circle = pygame.draw.circle(screen, 'black', (center_x, center_y), 20, 2)
    draw_player()
    blinky = Ghost(blinky_x, blinky_y, targets[0], ghost_speeds[0], blinky_img, blinky_direction, blinky_dead,
                   blinky_box, 0)
    inky = Ghost(inky_x, inky_y, targets[1], ghost_speeds[1], inky_img, inky_direction, inky_dead,
                 inky_box, 1)
    pinky = Ghost(pinky_x, pinky_y, targets[2], ghost_speeds[2], pinky_img, pinky_direction, pinky_dead,
                  pinky_box, 2)
    clyde = Ghost(clyde_x, clyde_y, targets[3], ghost_speeds[3], clyde_img, clyde_direction, clyde_dead,
                  clyde_box, 3)
    draw_misc()
    targets = get_targets(blinky_x, blinky_y, inky_x, inky_y, pinky_x, pinky_y, clyde_x, clyde_y)

    turns_allowed = check_position(center_x, center_y)
    if moving:
        player_x, player_y = move_player(player_x, player_y)
        if not blinky_dead and not blinky.in_box:
            blinky_x, blinky_y, blinky_direction = blinky.move_blinky()
        else:
            blinky_x, blinky_y, blinky_direction = blinky.move_clyde()
        if not pinky_dead and not pinky.in_box:
            pinky_x, pinky_y, pinky_direction = pinky.move_pinky()
        else:
            pinky_x, pinky_y, pinky_direction = pinky.move_clyde()
        if not inky_dead and not inky.in_box:
            inky_x, inky_y, inky_direction = inky.move_inky()
        else:
            inky_x, inky_y, inky_direction = inky.move_clyde()
        clyde_x, clyde_y, clyde_direction = clyde.move_clyde()
    score, powerup, power_counter, eaten_ghost = check_collisions(score, powerup, power_counter, eaten_ghost)
    # add to if not powerup to check if eaten ghosts
    if not powerup:
        if (player_circle.colliderect(blinky.rect) and not blinky.dead) or \
                (player_circle.colliderect(inky.rect) and not inky.dead) or \
                (player_circle.colliderect(pinky.rect) and not pinky.dead) or \
                (player_circle.colliderect(clyde.rect) and not clyde.dead):
            if lives > 0:
                lives -= 1
                startup_counter = 0
                powerup = False
                power_counter = 0
                player_x = 450
                player_y = 663
                direction = 0
                direction_command = 0
                blinky_x = 56
                blinky_y = 58
                blinky_direction = 0
                inky_x = 440
                inky_y = 388
                inky_direction = 2
                pinky_x = 440
                pinky_y = 438
                pinky_direction = 2
                clyde_x = 440
                clyde_y = 438
                clyde_direction = 2
                eaten_ghost = [False, False, False, False]
                blinky_dead = False
                inky_dead = False
                clyde_dead = False
                pinky_dead = False
            else:
                if is_top_10(score, scoreboard):
                    entering_name = True
                    game_over = False
                else:
                    game_over = True
                moving = False
                startup_counter = 0
    if powerup and player_circle.colliderect(blinky.rect) and eaten_ghost[0] and not blinky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 56
            blinky_y = 58
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghost = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
        else:
            if is_top_10(score, scoreboard):
                entering_name = True
                game_over = False
            else:
                game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(inky.rect) and eaten_ghost[1] and not inky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 56
            blinky_y = 58
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghost = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
        else:
            if is_top_10(score, scoreboard):
                entering_name = True
                game_over = False
            else:
                game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(pinky.rect) and eaten_ghost[2] and not pinky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 56
            blinky_y = 58
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghost = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
        else:
            if is_top_10(score, scoreboard):
                entering_name = True
                game_over = False
            else:
                game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(clyde.rect) and eaten_ghost[3] and not clyde.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 56
            blinky_y = 58
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghost = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
        else:
            if is_top_10(score, scoreboard):
                entering_name = True
                game_over = False
            else:
                game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(blinky.rect) and not blinky.dead and not eaten_ghost[0]:
        blinky_dead = True
        eaten_ghost[0] = True
        score += (2 ** eaten_ghost.count(True)) * 100
    if powerup and player_circle.colliderect(inky.rect) and not inky.dead and not eaten_ghost[1]:
        inky_dead = True
        eaten_ghost[1] = True
        score += (2 ** eaten_ghost.count(True)) * 100
    if powerup and player_circle.colliderect(pinky.rect) and not pinky.dead and not eaten_ghost[2]:
        pinky_dead = True
        eaten_ghost[2] = True
        score += (2 ** eaten_ghost.count(True)) * 100
    if powerup and player_circle.colliderect(clyde.rect) and not clyde.dead and not eaten_ghost[3]:
        clyde_dead = True
        eaten_ghost[3] = True
        score += (2 ** eaten_ghost.count(True)) * 100

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                direction_command = 0
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                direction_command = 1
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                direction_command = 2
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                direction_command = 3
            if event.key == pygame.K_SPACE and game_over:
                powerup = False
                power_counter = 0
                lives -= 1
                startup_counter = 0
                player_x = 450
                player_y = 663
                direction = 0
                direction_command = 0
                blinky_x = 56
                blinky_y = 58
                blinky_direction = 0
                inky_x = 440
                inky_y = 388
                inky_direction = 2
                pinky_x = 440
                pinky_y = 438
                pinky_direction = 2
                clyde_x = 440
                clyde_y = 438
                clyde_direction = 2
                eaten_ghost = [False, False, False, False]
                blinky_dead = False
                inky_dead = False
                clyde_dead = False
                pinky_dead = False
                score = 0
                lives = 3
                level = copy.deepcopy(boards)
                game_over = False
                current_level = 1

        if event.type == pygame.KEYUP:
            if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and direction_command == 0:
                direction_command = direction
            if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and direction_command == 1:
                direction_command = direction
            if (event.key == pygame.K_UP or event.key == pygame.K_w) and direction_command == 2:
                direction_command = direction
            if (event.key == pygame.K_DOWN or event.key == pygame.K_s) and direction_command == 3:
                direction_command = direction

    if direction_command == 0 and turns_allowed[0]:
        direction = 0
    if direction_command == 1 and turns_allowed[1]:
        direction = 1
    if direction_command == 2 and turns_allowed[2]:
        direction = 2
    if direction_command == 3 and turns_allowed[3]:
        direction = 3

    if player_x > 900:
        player_x = -47
    elif player_x < -50:
        player_x = 897

    if blinky.in_box and blinky_dead:
        blinky_dead = False
    if inky.in_box and inky_dead:
        inky_dead = False
    if pinky.in_box and pinky_dead:
        pinky_dead = False
    if clyde.in_box and clyde_dead:
        clyde_dead = False

    pygame.display.flip()
pygame.quit()


# zvukové efekty, restart a hlášky o výhře
