import logging
import time
import pathlib

import git 

import pygame

from pyfiglet import Figlet

from hotreload import Loader

import adafruit_dht
import board

GIT_REFRESH_INTERVAL = 300

if __name__ == "__main__":
  logging.basicConfig(filename='clocko.log',
                      format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
                      filemode='a',
                      level=logging.DEBUG)
  logger = logging.getLogger('main')
  figl = Figlet(font='larry3d')
  banner = figl.renderText("hello delphi")
  logger.info("\n" + banner)

  script = Loader("runloop.py")

  pygame.init()

  size = width, height = 480, 800
  pygame.display.init()
  logger.debug(pygame.display.Info())
  screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
  pygame.mouse.set_visible(False)

  last_weather_check = 0
  weather = None

  last_git_check = 0
  git_repo = git.Repo(pathlib.Path(__file__).parent.absolute())

  last_background_update = 0
  background_details = None

  dhtDevice = adafruit_dht.DHT11(board.D27)
  last_ambient_check = 0
  ambient = None

  while True:
    if time.time() - last_git_check > GIT_REFRESH_INTERVAL:
      logger.info("updating git repo...")
      git_repo.remotes.origin.pull()
      last_git_check = time.time()
      logger.info("set last git pull to %s" %last_git_check)

    new_weather = script.weather_updater(last_weather_check)
    if new_weather is not None:
      last_weather_check = time.time()
      weather = new_weather
      logger.info("got new weather, set last check time to %s" % last_weather_check)

    new_ambient = script.ambient_updater(last_ambient_check, dhtDevice)
    if new_ambient is not None:
      last_ambient_check = time.time()
      ambient = new_ambient
      logger.info("got new ambient, set last check time to %s" % last_ambient_check)

    new_bg = script.background_updater(last_background_update)
    if new_bg is not None:
      last_background_update = time.time()
      background_details = new_bg
      logger.info("updating background at %s" % last_background_update)

    script.run(screen, weather, ambient, background_details)

    time.sleep(1)