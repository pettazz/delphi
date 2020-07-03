import logging
import time, datetime
import pathlib
import signal
import sys
import os
import json
import random

import requests
import git 
import hupper
from tzlocal import get_localzone

import pygame
from pygame.locals import *

from PIL import Image

from pyfiglet import Figlet

try:
    import board
    import RPi.GPIO as GPIO
    import adafruit_dht
    DHT_SUPPORT = True
except NotImplementedError:
    DHT_SUPPORT = False

from statictools import * 

FULLSCREEN_MODE = 0
GIT_REFRESH_INTERVAL = 300

class Delphi:
  def __init__(self):
    self.logger = logging.getLogger('delphi')
    log_formatter = logging.Formatter("%(asctime)s %(name)s.%(funcName)s [%(levelname)s] %(message)s")

    handler = logging.FileHandler('clocko.log')
    handler.setFormatter(log_formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(level=LOGLEVEL)

    figl = Figlet(font='larry3d')
    banner = figl.renderText("hello delphi")
    self.logger.info("\n" + banner)

    signal.signal(signal.SIGINT, self.quitter)
    signal.signal(signal.SIGTERM, self.quitter)

    pygame.init()

    size = width, height = 480, 800
    pygame.display.init()
    os.environ['SDL_VIDEODRIVER'] = 'fbcon'
    os.environ['SDL_FBDEV'] = '/dev/fb0'
    self.logger.debug(pygame.display.Info())
    self.logger.debug("SDL_VIDEODRIVER: %s" % os.getenv("SDL_VIDEODRIVER"))
    self.logger.debug("SDL_FBDEV: %s" % os.getenv("SDL_FBDEV"))
    try:
        self.screen = pygame.display.set_mode(size, FULLSCREEN_MODE)
    except:
        self.logger.critical('could not set mode on display', exc_info=True)
        self.quitter()
    pygame.mouse.set_visible(False)

    self.last_weather_check = 0
    self.weather = None

    self.last_git_check = 0
    self.git_repo = git.Repo(pathlib.Path(__file__).parent.absolute())

    self.last_background_update = 0
    self.background_details = None

    if DHT_SUPPORT:
      self.dhtDevice = adafruit_dht.DHT11(board.D27)
      self.last_ambient_check = 0
    self.ambient = None

    self.alive = True

  def weather_updater(self):
    weather = None
    if time.time() - self.last_weather_check > WEATHER_INTERVAL:
        self.logger.info('refreshing weather data...')
        try:
            one_hour_out = (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
            CLIMACELL_PARAMS['end_time'] = one_hour_out
            res = requests.get(CLIMACELL_NOWCAST, timeout=1, params=CLIMACELL_PARAMS)
            if res.status_code == 200:
                weather_raw = json.loads(res.text)

                with open('lol.json', 'w') as dumperoo:
                    dumperoo.write(str(weather_raw))

                # basics
                is_night = datetime.datetime.now(tz=datetime.timezone.utc) > datetime.datetime.fromisoformat(weather_raw[0]['sunset']['value'].replace('Z', '+00:00'))
                icon = WEATHER_ICONS_MAP['day' if not is_night else 'night'][weather_raw[0]['weather_code']['value']]

                # temp/feels like
                temp = int(weather_raw[0]['temp']['value'])
                feels_like = int(weather_raw[0]['feels_like']['value'])

                change_symbol = "+" if feels_like > temp else "-"
                margin = abs(temp - feels_like)
                feels_like_indicator = ""
                if margin > 0:
                    for interval in range(0, (margin // 5) + 1):
                        feels_like_indicator = feels_like_indicator + change_symbol

                self.logger.debug("feels like margin of %s, displaying %s" % (margin, feels_like_indicator))

                # next hour status 
                current = weather_raw[0]['weather_code']['value']
                inflections = []
                prev = current
                for idx, interval in enumerate(weather_raw):
                    if not interval['weather_code']['value'] == prev:
                        inflections.append(interval)
                        prev = interval['weather_code']['value']

                if inflections:
                    state = "something's gonna happen"
                else:
                    state = "%s for the hour" % WEATHER_CODES_TEXT[current]

                # high/low, is this even in the api?
                high = 90 #int(weather_raw[0]['weather_code']['value'])
                low = 70 #int(weather_raw[0]['weather_code']['value'])

                # humidity
                dewpoint = int(weather_raw[0]['dewpoint']['value'])
                if dewpoint <= 55:
                    humidity = 'low'
                elif dewpoint < 65:
                    humidity = 'medium'
                else:
                    humidity = 'high'

                if is_night:
                    sun_next = 'rise'
                    sun_time_iso = weather_raw[0]['sunrise']['value']
                else:
                    sun_next = 'set'
                    sun_time_iso = weather_raw[0]['sunset']['value']
                sun_dt = datetime.datetime.fromisoformat(sun_time_iso.replace('Z', '+00:00')).astimezone(get_localzone())
                sun_time = sun_dt.strftime("%I:%M")

                if sun_time[0] == "0":
                    sun_time = sun_time[1:]

                # wind
                wind_speed = int(weather_raw[0]['wind_speed']['value'])
                bearing = weather_raw[0]['wind_direction']['value']
                if bearing > 348.75 or bearing <= 33.75:
                    wind_direction = 'N'
                elif bearing > 33.75 and bearing <= 78.75:
                    wind_direction = 'NE'
                elif bearing > 78.75 and bearing <= 123.75:
                    wind_direction = 'E'
                elif bearing > 123.75 and bearing <= 168.75:
                    wind_direction = 'SE'
                elif bearing > 168.75 and bearing <= 213.75:
                    wind_direction = 'S'
                elif bearing > 213.75 and bearing <= 258.75:
                    wind_direction = 'SW'
                elif bearing > 258.75 and bearing <= 303.75:
                    wind_direction = 'W'
                elif bearing > 303.75 and bearing <= 348.75:
                    wind_direction = 'NW'

                # air quality
                aqi = weather_raw[0]['epa_aqi']['value']
                if aqi <= 50:
                    air_quality = 'good'
                    air_quality_color = 'green'
                elif aqi <= 100:
                    air_quality = 'moderate'
                    air_quality_color = 'yellow'
                elif aqi <= 150:
                    air_quality = 'bad'
                    air_quality_color = 'orange'
                elif aqi <= 200:
                    air_quality = 'unhealthy'
                    air_quality_color = 'red'
                elif aqi <= 300:
                    air_quality = 'very unhealthy'
                    air_quality_color = 'purple'
                else:
                    air_quality = 'hazardous'
                    air_quality_color = 'maroon'
                
                # pollen
                tree_pollen = weather_raw[0]['pollen_tree']['value']
                tree_pollen = tree_pollen if tree_pollen is not None else 0
                tree_pollen_color = POLLEN_COLOR_SCALE[tree_pollen]

                weed_pollen = weather_raw[0]['pollen_weed']['value']
                weed_pollen = weed_pollen if weed_pollen is not None else 0
                weed_pollen_color = POLLEN_COLOR_SCALE[weed_pollen]

                grass_pollen = weather_raw[0]['pollen_grass']['value']
                grass_pollen = grass_pollen if grass_pollen is not None else 0
                grass_pollen_color = POLLEN_COLOR_SCALE[grass_pollen]

                weather = {
                    'temp': temp,
                    'is_night': is_night,
                    'icon': icon,
                    'feels_like': feels_like,
                    'feels_like_indicator': feels_like_indicator,
                    'state': state,
                    'high': high,
                    'low': low,
                    'dewpoint': dewpoint,
                    'humidity': humidity,
                    'sun_time': sun_time,
                    'sun_next': sun_next,
                    'wind_speed': wind_speed,   
                    'wind_direction': wind_direction,
                    'air_quality': air_quality,
                    'air_quality_color': air_quality_color,
                    'tree_pollen_color': tree_pollen_color,
                    'weed_pollen_color': weed_pollen_color,
                    'grass_pollen_color': grass_pollen_color
                }

                self.last_weather_check = time.time()

                self.logger.info("successfully fetched new weather, current time: %s" % weather_raw[0]['observation_time']['value'])
                self.logger.info("got new weather, set last check time to %s" % self.last_weather_check)
        except Exception as e:
            self.logger.warning("failed to fetch weather, guess we'll try next tick", exc_info=True)

    return weather

  def ambient_updater(self):
    ambient = None

    if DHT_SUPPORT:
      if time.time() - self.last_ambient_check > AMBIENT_INTERVAL:
          self.logger.info('refreshing ambient data...')
          try:
              tempf = self.dhtDevice.temperature * (9 / 5) + 32
              humidity = self.dhtDevice.humidity

              ambient = {
                  "temperature": "{:.1f}".format(tempf),
                  "humidity": humidity
              }
              self.last_ambient_check = time.time()

              self.logger.info("got new ambient, set last check time to %s" % self.last_ambient_check)
              self.logger.info("successfully fetched new ambient readings: %s" % ambient)
          except Exception as e:
              self.logger.warning("failed to fetch ambient, guess we'll try next tick")
              self.logger.warning(e)
    else:

      ambient = {
          "temperature": "{:.1f}".format(80),
          "humidity": "27"
      }
      self.logger.info("DHT support disabled, using fake data")

    return ambient

  def background_updater(self):
    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800
    SCREEN_WIDTH_CORRECTION = 80 # the pixels are wrong? wat da fuk

    background_details = None

    if time.time() - self.last_background_update > BACKGROUND_INTERVAL:
        self.logger.info('updating background...')

        backgrounds = [image for image in os.listdir(BACKGROUND_PATH) if image.endswith(".jpg")]
        image_name = random.choice(backgrounds)
        img = pygame.image.load(BACKGROUND_PATH + image_name)

        img_width, img_height = img.get_size()
        if round(img_width / img_height, 3) > 0.6:
            new_height = SCREEN_HEIGHT
            new_width = ((new_height * img_width) // img_height) + SCREEN_WIDTH_CORRECTION
        else:
            new_width = SCREEN_WIDTH + SCREEN_WIDTH_CORRECTION
            new_height = (new_width * img_height) // img_width

        background = pygame.transform.smoothscale(img, (new_width, new_height))
      
        width_offset = (SCREEN_WIDTH // 2) - (new_width // 2)
        height_offset = (SCREEN_HEIGHT // 2) - (new_height // 2)

        background_details = {
            "image": background,
            "offset": (width_offset, height_offset)
        }
        self.last_background_update = time.time()
        
        self.logger.info("updating background at %s" % self.last_background_update)
        self.logger.info('new background: %s (%sx%s) offset (%s, %s)' % (image_name, new_width, new_height, width_offset, height_offset))

    return background_details

  def draw_screen(self, weather, ambient, background):
    text_color = (255, 255, 255)
    if background is not None:
        self.screen.blit(background['image'], (background['offset'][0], background['offset'][1]))

    now_time = time.strftime("%I:%M")
    now_date = time.strftime("%A, %B %-d")

    if now_time[0] == "0":
        now_time = now_time[1:]

    header_shadowed(self.screen, now_time, (242, 132), 210, text_color)
    header_shadowed(self.screen, now_date, (242, 232), 45, text_color)

    if weather is not None:
        # main
        fa_text_shadowed(self.screen, weather['icon'], (175, 507), 90, text_color)
        header_shadowed(self.screen, str(weather['temp']) + "°", (305, 510), 100, text_color)
        body_text_shadowed(self.screen, weather['feels_like_indicator'], (340, 500), 35, text_color)
        header_shadowed(self.screen, weather['state'], (242, 575), 35, text_color)

        # hi/low
        fa_text_shadowed(self.screen, 'angle-up', (120, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['high']) + "°", (137, 600), 25, text_color)
        fa_text_shadowed(self.screen, 'angle-down', (190, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['low']) + "°", (207, 600), 25, text_color)

        # dewpoint
        fa_text_shadowed(self.screen, 'tint', (280, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['dewpoint']) + "°", (305, 600), 25, text_color)
        if weather['humidity'] == 'low':
            humidity_icon = 'smile'
        elif weather['humidity'] == 'medium':
            humidity_icon = 'meh'
        elif weather['humidity'] == 'high':
            humidity_icon = 'frown-open'
        fa_text_shadowed(self.screen, humidity_icon, (345, 603), 23, text_color, "left")

        # sunrise/set
        if weather['sun_next'] == 'rise':
            sun_icon = 'sun'
        else:
            sun_icon = 'moon'
        fa_text_shadowed(self.screen, sun_icon, (120, 640), 20, text_color, "left")
        body_text_shadowed(self.screen, weather['sun_time'], (145, 635), 25, text_color)

        # wind
        fa_text_shadowed(self.screen, 'wind', (260, 640), 20, text_color, "left")
        body_text_shadowed(self.screen, str(weather['wind_speed']), (293, 650), 25, text_color, "center")
        body_text_shadowed(self.screen, " mph", (303, 641), 17, text_color)
        body_text_shadowed(self.screen, str(weather['wind_direction']), (340, 635), 25, text_color) # an icon someday

        # pollen / aqi
        fa_text_shadowed(self.screen, 'tree', (120, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (137, 680), 20, COLOR_RGB[weather['tree_pollen_color']], "left")
        fa_text_shadowed(self.screen, 'leaf', (170, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (197, 680), 20, COLOR_RGB[weather['weed_pollen_color']], "left")
        fa_text_shadowed(self.screen, 'seedling', (230, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (253, 680), 20, COLOR_RGB[weather['grass_pollen_color']], "left")

        # aqi
        fa_text_shadowed(self.screen, 'industry', (325, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (348, 680), 20, COLOR_RGB[weather['air_quality_color']], "left")

    if ambient is not None:
        fa_text_shadowed(self.screen, 'microchip', (170, 733), 20, text_color, "left")
        body_text_shadowed(self.screen, "%s° /  %s%%" % (ambient['temperature'], ambient['humidity']), (200, 730), 25, text_color)
        
    pygame.display.flip()

  def runner(self):
    weather = None
    ambient = None
    background_details = None

    while self.alive:
      for event in pygame.event.get():
          if event.type == pygame.QUIT:
              self.quitter(msg='pygame QUIT event')
          if event.type == KEYDOWN:
              if event.key == K_ESCAPE:
                  self.quitter(msg='ESC key')
              if event.key == K_RIGHT:
                  self.last_background_update = 0
                  self.logger.info('next background...')

      if time.time() - self.last_git_check > GIT_REFRESH_INTERVAL:
        self.logger.info("updating git repo...")
        self.git_repo.remotes.origin.pull()
        self.last_git_check = time.time()
        self.logger.info("set last git pull to %s" % self.last_git_check)

      new_weather = self.weather_updater()
      if new_weather is not None:
        weather = new_weather

      
      new_ambient = self.ambient_updater()
      if new_ambient is not None:
          ambient = new_ambient
          
      new_bg = self.background_updater()
      if new_bg is not None:
        background_details = new_bg

      self.draw_screen(weather, ambient, background_details)

      time.sleep(1)

  def quitter(self, signum=None, frame=None, msg=None):
    if signum:
      self.logger.info('caught signal %s, ending runloop' % signum)
    if msg:
      self.logger.info('killed by %s, ending runloop' % msg)
    self.alive = False
    
    self.logger.info('goodbye!')
    self.dhtDevice = None
    GPIO.cleanup()
    pygame.display.quit()
    pygame.quit()
    sys.exit()

def main():
  reloader = hupper.start_reloader('delphi.main')
  reloader.watch_files([
    'statictools.py',
    'assets/*'
  ])

  d = Delphi()
  d.runner()

if __name__ == "__main__":
  main()