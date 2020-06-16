import logging
import time
import pathlib
import signal

import git 

import pygame

from pyfiglet import Figlet

from hotreload import Loader

import adafruit_dht
try:
    import board
    DHT_SUPPORT = True
except NotImplementedError:
    DHT_SUPPORT = False

logging.basicConfig(filename='clocko.log',
                    format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
                    filemode='a',
                    level=logging.DEBUG)

FULLSCREEN_MODE = 0
GIT_REFRESH_INTERVAL = 300

class Delphi:
  def __init__(self):
    logger = logging.getLogger('init')

    figl = Figlet(font='larry3d')
    banner = figl.renderText("hello delphi")
    logger.info("\n" + banner)

    self.script = Loader("runloop.py")

    pygame.init()

    signal.signal(signal.SIGINT, self.quitter)
    signal.signal(signal.SIGTERM, self.quitter)

    size = width, height = 480, 800
    pygame.display.init()
    logger.debug(pygame.display.Info())
    self.screen = pygame.display.set_mode(size, FULLSCREEN_MODE)
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

  def runner(self):
    logger = logging.getLogger('runner')

    weather = None
    ambient = None
    background_details = None

    while self.alive:
      if time.time() - self.last_git_check > GIT_REFRESH_INTERVAL:
        logger.info("updating git repo...")
        self.git_repo.remotes.origin.pull()
        self.last_git_check = time.time()
        logger.info("set last git pull to %s" % self.last_git_check)

      new_weather = self.script.weather_updater(self.last_weather_check)
      if new_weather is not None:
        self.last_weather_check = time.time()
        weather = new_weather
        logger.info("got new weather, set last check time to %s" % self.last_weather_check)

      if DHT_SUPPORT:
        new_ambient = self.script.ambient_updater(self.last_ambient_check, self.dhtDevice)
        if new_ambient is not None:
          self.last_ambient_check = time.time()
          ambient = new_ambient
          logger.info("got new ambient, set last check time to %s" % self.last_ambient_check)

      new_bg = self.script.background_updater(self.last_background_update)
      if new_bg is not None:
        self.last_background_update = time.time()
        background_details = new_bg
        logger.info("updating background at %s" % self.last_background_update)

      self.script.run(self.screen, weather, ambient, background_details)

      time.sleep(1)

  def quitter(self, signum, frame):
    logger = logging.getLogger('quitter')
    logger.info('caught signal %s, ending runloop' % signum)
    self.alive = False

if __name__ == "__main__":
  d = Delphi()
  d.runner()
