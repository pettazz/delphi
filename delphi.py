import logging
import time
import pathlib
import signal
import sys
import os
import json
import random

import requests
import git 
import hupper

import pygame
from pygame.locals import *

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
            res = requests.get(DARKSKY_FORECAST, timeout=1)
            if res.status_code == 200:
                weather = json.loads(res.text)
                self.last_weather_check = time.time()

                self.logger.info("successfully fetched new weather, timestamp: %s" % weather['currently']['time'])
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
      self.logger.info("DHT support disabled.")

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
        if img_width < img_height:
            new_width = SCREEN_WIDTH + SCREEN_WIDTH_CORRECTION
            new_height = (new_width * img_height) // img_width
        else:
            new_height = SCREEN_HEIGHT
            new_width = ((new_height * img_width) // img_height) + SCREEN_WIDTH_CORRECTION

        background = pygame.transform.scale(img, (new_width, new_height))
      
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
    if background is not None:
        self.screen.blit(background['image'], (background['offset'][0], background['offset'][1]))

    now_time = time.strftime("%I:%M")
    now_date = time.strftime("%A, %B %-d")

    if now_time[0] == "0":
        now_time = now_time[1:]

    text_shadow(self.screen, now_time, (242, 202), 200, (255, 255, 255))
    text_shadow(self.screen, now_date, (242, 302), 45, (255, 255, 255))

    if ambient is not None:
        fa_text_shadow(self.screen, 'tachometer-alt', (372, 472), 65, (255, 255, 255), "left")
        text_shadow(self.screen, "Temperature: %s°F" % ambient['temperature'], (52, 472), 30, (255, 255, 255), "left")
        text_shadow(self.screen, "Humidity: %s%%" % ambient['humidity'], (52, 502), 30, (255, 255, 255), "left")

    if weather is not None:
        icon = WEATHER_ICON_MAP[weather['currently']['icon']]
        temp = int(weather['currently']['temperature'])
        feels = int(weather['currently']['apparentTemperature'])
        precipProb = int(weather['currently']['precipProbability'] * 100)
        hour_summary = weather['minutely']['summary']

        text1 = "%s°, feels like %s°, %s%% precip" % (temp, feels, precipProb)
        text2 = hour_summary

        fa_text_shadow(self.screen, icon, (32, 572), 65, (255, 255, 255), "left")
        text_shadow(self.screen, text1, (122, 572), 30, (255, 255, 255), "left")
        text_shadow(self.screen, text2, (122, 602), 30, (255, 255, 255), "left")

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

      if time.time() - self.last_git_check > GIT_REFRESH_INTERVAL:
        self.logger.info("updating git repo...")
        self.git_repo.remotes.origin.pull()
        self.last_git_check = time.time()
        self.logger.info("set last git pull to %s" % self.last_git_check)

      new_weather = self.weather_updater()
      if new_weather is not None:
        weather = new_weather

      if DHT_SUPPORT:
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