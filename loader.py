import logging
import time
import pathlib
import signal

import git 

import pygame

from pyfiglet import Figlet

from hotreload import Loader

import adafruit_dht
import board

GIT_REFRESH_INTERVAL = 300

class Delphi:
  def __init__(self):
    logging.basicConfig(filename='clocko.log',
                        format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
                        filemode='a',
                        level=logging.DEBUG)

    self.logger = logging.getLogger('main')
    figl = Figlet(font='larry3d')
    banner = figl.renderText("hello delphi")
    self.logger.info("\n" + banner)

    self.script = Loader("runloop.py")

    pygame.init()

    signal.signal(signal.SIGINT, self.quitter)
    signal.signal(signal.SIGTERM, self.quitter)

    size = width, height = 480, 800
    pygame.display.init()
    self.logger.debug(pygame.display.Info())
    self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)

    self.last_weather_check = 0
    self.weather = None

    self.last_git_check = 0
    self.git_repo = git.Repo(pathlib.Path(__file__).parent.absolute())

    self.last_background_update = 0
    self.background_details = None

    self.dhtDevice = adafruit_dht.DHT11(board.D27)
    self.last_ambient_check = 0
    self.ambient = None

    self.alive = True

  def runner(self):
    while self.alive:
      if time.time() - self.last_git_check > GIT_REFRESH_INTERVAL:
        self.logger.info("updating git repo...")
        self.git_repo.remotes.origin.pull()
        self.last_git_check = time.time()
        self.logger.info("set last git pull to %s" % self.last_git_check)

      new_weather = self.script.weather_updater(self.last_weather_check)
      if new_weather is not None:
        self.last_weather_check = time.time()
        weather = new_weather
        self.logger.info("got new weather, set last check time to %s" % self.last_weather_check)

      new_ambient = self.script.ambient_updater(self.last_ambient_check, self.dhtDevice)
      if new_ambient is not None:
        self.last_ambient_check = time.time()
        ambient = new_ambient
        self.logger.info("got new ambient, set last check time to %s" % self.last_ambient_check)

      new_bg = self.script.background_updater(self.last_background_update)
      if new_bg is not None:
        self.last_background_update = time.time()
        background_details = new_bg
        self.logger.info("updating background at %s" % self.last_background_update)

      self.script.run(self.screen, weather, ambient, background_details)

      time.sleep(1)

  def quitter(self, signum, frame):
    self.logger('caught signal %s, ending runloop' % signum)
    self.alive = False

if __name__ == "__main__":
  d = Delphi()
  d.runner()
