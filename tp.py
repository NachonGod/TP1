import pygame, math, random, sys, json, os
from datetime import datetime

pygame.init()
try:    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except: pass

SW, SH = 1280, 720
screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE)
pygame.display.set_caption("Slither.io - TP")
clock = pygame.time.Clock()
FPS   = 60

WORLD            = 3000
FOOD_COUNT       = 220
SPEED            = 2.8
TURN_SPEED       = 0.065
INITIAL_SEGMENTS = 6
RADIUS_BASE      = 4
RADIUS_MAX       = 12

SCORES_FILE = "resultados.json"

BG         = (5,  10, 14)
BORDER_COL = (255, 45, 120)
TEXT_COL   = (200, 255, 220)
DIVIDER    = (0, 255, 136)

PLAYER_COLORS = [
    {"head": (0, 255, 136),  "body": (0, 180, 90),   "name": "Jugador 1"},
    {"head": (0, 200, 255),  "body": (0, 130, 180),  "name": "Jugador 2"},
    {"head": (255, 45, 120), "body": (160, 20, 70),  "name": "Jugador 3"},
    {"head": (255, 220, 0),  "body": (180, 150, 0),  "name": "Jugador 4"},
]

FOOD_COLORS = [
    (255,45,120),(0,255,136),(0,200,255),(255,220,0),(255,120,0),(180,80,255),
]

CONTROLS = [
    {"up":pygame.K_w,   "down":pygame.K_s,    "left":pygame.K_a,    "right":pygame.K_d    },
    {"up":pygame.K_UP,  "down":pygame.K_DOWN, "left":pygame.K_LEFT, "right":pygame.K_RIGHT},
    {"up":pygame.K_t,   "down":pygame.K_g,    "left":pygame.K_f,    "right":pygame.K_h    },
    {"up":pygame.K_i,   "down":pygame.K_k,    "left":pygame.K_j,    "right":pygame.K_l    },
]

try:
    FONT_BIG = pygame.font.SysFont("couriernew", 72, bold=True)
    FONT_MED = pygame.font.SysFont("couriernew", 36, bold=True)
    FONT_SM  = pygame.font.SysFont("couriernew", 22)
    FONT_XS  = pygame.font.SysFont("couriernew", 16)
except:
    FONT_BIG = FONT_MED = FONT_SM = FONT_XS = pygame.font.SysFont(None, 36)