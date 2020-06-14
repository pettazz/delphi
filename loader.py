import logging
import time
import pathlib

import git 

import pygame

from hotreload import Loader

GIT_REFRESH_INTERVAL = 300

if __name__ == "__main__":
  logging.basicConfig(filename='clocko.log',
                      format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
                      filemode='a',
                      level=logging.DEBUG)
  logger = logging.getLogger('main')

  script = Loader("runloop.py")

  pygame.init()

  size = width, height = 480, 800
  pygame.display.init()
  screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

  pygame.mouse.set_visible(False)

  img = pygame.image.load('/home/pi/botson.jpg')
  background = pygame.transform.scale(img, (1066, 800))

  last_weather_check = 0
  weather = None

  last_git_check = 0
  git_repo = git.Repo(pathlib.Path(__file__).parent.absolute())

  while True:
    if time.time() - last_git_check > GIT_REFRESH_INTERVAL:
      git_repo.remotes.origin.pull()
      last_git_check = time.time()

    new_weather = script.weather_updater(last_weather_check)
    if new_weather is not None:
      last_weather_check = time.time()
      weather = new_weather
      logger.info("got new weather, set last check time to %s" % last_weather_check)

    script.run(screen, background, weather)
    
    time.sleep(1)