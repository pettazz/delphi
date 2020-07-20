import logging

from secrets import *

import arrow
import requests
import fontawesome as fa
from ics import Calendar, Event
from tzlocal import get_localzone

import pygame
from pygame.locals import *

LOGLEVEL = logging.DEBUG

AMBIENT_INTERVAL = 120
WEATHER_INTERVAL_REALTIME = 180
WEATHER_INTERVAL_FORECAST = 300
BACKGROUND_INTERVAL = 300
CALENDAR_INTERVAL = 3600
BACKGROUND_PATH = "assets/img/backgrounds/"
COLOR_RGB = {
  'red': (255, 0, 0),
  'orange': (255, 85, 0),
  'yellow-orange': (255, 180, 0),
  'yellow': (255, 255, 0),
  'yellow-green': (180, 255, 0),
  'green': (0, 255, 0),
  'purple': (128, 0, 128),
  'maroon': (128, 0, 0)
}
POLLEN_COLOR_SCALE = {
  0: 'green',
  1: 'yellow-green',
  2: 'yellow',
  3: 'yellow-orange',
  4: 'orange',
  5: 'red'
}
CLIMACELL_FIELDS = [
  'precipitation',
  'precipitation_type',
  'temp',
  'feels_like',
  'dewpoint',
  'wind_speed',
  'wind_direction',
  'sunrise',
  'sunset',
  'weather_code',
  'pollen_tree',
  'pollen_grass',
  'pollen_weed',
  'epa_aqi'
]
CLIMACELL_PARAMS = {
  'apikey': CLIMACELL_API_KEY,
  'lat': LATLONG[0],
  'lon': LATLONG[1],
  'unit_system': 'us',
  'fields': CLIMACELL_FIELDS
}
CLIMACELL_NOWCAST  = 'https://api.climacell.co/v3/weather/nowcast'
CLIMACELL_REALTIME  = 'https://api.climacell.co/v3/weather/realtime'
WEATHER_CODES_TEXT = {
  'rain_heavy': 'heavy rain',
  'rain': 'rain',
  'freezing_rain_heavy': 'heavy freezing rain',
  'freezing_rain': 'freezing rain',
  'freezing_rain_light': 'light freezing rain',
  'freezing_drizzle': 'freezing drizzle',
  'ice_pellets_heavy': 'heavy ice',
  'ice_pellets': 'ice',
  'ice_pellets_light': 'light ice',
  'snow_heavy': 'heavy snow',
  'snow': 'snow',
  'snow_light': 'light snow',
  'flurries': 'flurries',
  'tstorm': 'thunderstorm',
  'fog_light': 'light fog',
  'fog': 'fog',
  'cloudy': 'cloudy',
  'mostly_cloudy': 'mostly cloudy',
  'partly_cloudy': 'partly cloudy',
  'mostly_clear': 'mostly clear',
  'clear': 'clear',
  'rain_light': 'light rain',
  'drizzle': 'drizzle'
}
WEATHER_ICONS_MAP = {
  'base': {
    'rain_heavy': 'cloud-rain',
    'rain': 'cloud-rain',
    'freezing_rain_heavy': 'cloud-showers-heavy',
    'freezing_rain': 'cloud-showers-heavy',
    'freezing_rain_light': 'cloud-showers-heavy',
    'freezing_drizzle': 'cloud-rain',
    'ice_pellets_heavy': 'cloud-showers-heavy',
    'ice_pellets': 'cloud-showers-heavy',
    'ice_pellets_light': 'cloud-showers-heavy',
    'snow_heavy': 'snowflake',
    'snow': 'snowflake',
    'snow_light': 'snowflake',
    'flurries': 'snowflake',
    'tstorm': 'bolt',
    'fog_light': 'smog',
    'fog': 'smog',
    'cloudy': 'cloud',
    'mostly_cloudy': 'cloud',
    'partly_cloudy': 'cloud',
    'mostly_clear': 'cloud',
    'clear': 'sun',
    'rain_light': 'cloud-rain',
    'drizzle': 'cloud-rain'
  }
}

WEATHER_ICONS_DAY = {
  'mostly_cloudy': 'cloud-sun',
  'partly_cloudy': 'cloud-sun',
  'mostly_clear': 'cloud-sun',
  'clear': 'sun',
  'rain_light': 'cloud-sun-rain',
  'drizzle': 'cloud-sun-rain'
}

WEATHER_ICONS_NIGHT = {
  'mostly_cloudy': 'cloud-moon',
  'partly_cloudy': 'cloud-moon',
  'mostly_clear': 'cloud-moon',
  'clear': 'moon',
  'rain_light': 'cloud-moon-rain',
  'drizzle': 'cloud-moon-rain'
}

WEATHER_ICONS_MAP['day'] = {**WEATHER_ICONS_MAP['base'], **WEATHER_ICONS_DAY}
WEATHER_ICONS_MAP['night'] = {**WEATHER_ICONS_MAP['base'], **WEATHER_ICONS_NIGHT}

EVENTS_TYPE_FA_ICONS = {
    'running': 'running',
    'sweeping': 'road',
    'birthday': 'birthday-cake',
    'medicine': 'capsules',
    'shared': 'calendar-alt',
    'default': 'calendar-day'
}

def _textgen(screen, text, position, size, color, align, font):
    text_obj = font.render(text, 1, color)
    textpos = text_obj.get_rect()
    if align == "left":
        textpos.topleft = position
    elif align == "right":
        textpos.topright = position
    else:
        textpos.center = position
    screen.blit(text_obj, textpos)

def header(screen, text, position, size, color, align="center"):
    font = pygame.font.Font('assets/font/Staatliches-Regular.ttf', size)
    _textgen(screen, text, position, size, color, align, font)

def header_shadowed(screen, text, position, size, color, align="center", shadow_color=(0, 0, 0)):
    header(screen, text, position, size, shadow_color, align)
    header(screen, text, (position[0] - 2, position[1] - 2), size, color, align)

def body_text(screen, text, position, size, color, align="left"):
    font = pygame.font.Font('assets/font/Staatliches-Regular.ttf', size)
    _textgen(screen, text, position, size, color, align, font)

def body_text_shadowed(screen, text, position, size, color, align="left", shadow_color=(0, 0, 0)):
    body_text(screen, text, position, size, shadow_color, align)
    body_text(screen, text, (position[0] - 2, position[1] - 2), size, color, align)

def fa_text(screen, name, position, size, color, align="center"):
    font = pygame.font.Font('assets/font/fa-solid-900.ttf', size)
    _textgen(screen, fa.icons[name], position, size, color, align, font)

def fa_text_shadowed(screen, name, position, size, color, align="center", shadow_color=(0, 0, 0)):
    fa_text(screen, name, position, size, shadow_color, align)
    fa_text(screen, name, (position[0] - 2, position[1] - 2), size, color, align)

def fullscreen_message(screen, message, color):
    screen.fill((0, 0, 0))
    header(screen, message, (240, 400), 30, color)

def fa_prefixed_text(screen, icon_name, text, position, size, color, align="center"):
    FA_OFFSET_Y = -3
    FA_SPACING = 5

    fa_font = pygame.font.Font('assets/font/fa-solid-900.ttf', size)
    body_font = pygame.font.Font('assets/font/Staatliches-Regular.ttf', size)

    fa_obj = fa_font.render(fa.icons[icon_name], 1, color)
    text_obj = body_font.render(text, 1, color)

    combo_surface = pygame.Surface((fa_obj.get_width() + FA_SPACING + text_obj.get_width(), fa_obj.get_height()), pygame.SRCALPHA)

    combo_surface.blit(fa_obj, (0, 0))
    combo_surface.blit(text_obj, (fa_obj.get_width() + FA_SPACING, FA_OFFSET_Y))

    da_rect = combo_surface.get_rect()

    if align == "left":
        da_rect.topleft = position
    elif align == "right":
        da_rect.topright = position
    else:
        da_rect.center = position

    screen.blit(combo_surface, da_rect)

def fa_prefixed_text_shadowed(screen, icon_name, text, position, size, color, align="center", shadow_color=(0, 0, 0)):
    fa_prefixed_text(screen, icon_name, text, position, size, shadow_color, align)
    fa_prefixed_text(screen, icon_name, text, (position[0] - 2, position[1] - 2), size, color, align)


def fetch_calendar(url):
    caltext = requests.get(url, timeout=1).text
    caltext = caltext.replace('BEGIN:VCALENDAR\r\n', 'BEGIN:VCALENDAR\r\nPRODID:-//Farts, Inc//NONSGML My Butt//EN\r\n', 1)

    return Calendar(caltext)

def get_calendar_events_today(url):
    calendar = fetch_calendar(url)
    today = arrow.now(get_localzone().zone).replace(hour=0, minute=0, second=0, microsecond=0)
    events = []

    for event in reversed(list(calendar.timeline)):
        if event.begin.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=get_localzone().zone) == today:
            events.append(event.name)

    return events

def get_calendar_events_tomorrow(url):
    calendar = fetch_calendar(url)
    tomorrow = arrow.now(get_localzone().zone).replace(hour=0, minute=0, second=0, microsecond=0).shift(days=1)
    events = []

    for event in reversed(list(calendar.timeline)):
        if event.begin.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=get_localzone().zone) == tomorrow:
            events.append(event.name)

    return events