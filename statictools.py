import fontawesome as fa

import pygame
from pygame.locals import *


BACKGROUND_INTERVAL = 300
BACKGROUND_PATH = "assets/img/backgrounds/"
WEATHER_INTERVAL = 300
DARKSKY_FORECAST = 'https://api.darksky.net/forecast/fd361ec0a4d4d24011a96cb6b47cd272/42.378920,-71.091040'
WEATHER_ICON_MAP = {
  'clear-day': 'sun',
  'clear-night': 'moon',
  'rain': 'cloud-rain',
  'snow': 'snowflake',
  'sleet': 'cloud-showers-heavy',
  'wind': 'wind',
  'fog': 'smog',
  'cloudy': 'cloud',
  'partly-cloudy-day': 'cloud-sun',
  'partly-cloudy-night': 'cloud-moon'
}

def _textgen(screen, text, position, size, color, align, font):
    text = font.render(text, 1, color)
    textpos = text.get_rect()
    if align == "left":
        textpos.topleft = position
    elif align == "right":
        textpos.topright = position
    else:
        textpos.center = position
    screen.blit(text, textpos)

def text(screen, text, position, size, color, align="center"):
    font = pygame.font.Font('assets/font/Staatliches-Regular.ttf', size)
    _textgen(screen, text, position, size, color, align, font)

def fa_text(screen, name, position, size, color, align="center"):
    font = pygame.font.Font('assets/font/fa-solid-900.ttf', size)
    _textgen(screen, fa.icons[name], position, size, color, align, font)

def fullscreen_message(screen, message, color):
    screen.fill((0, 0, 0))
    text(screen, message, (240, 400), 30, color)