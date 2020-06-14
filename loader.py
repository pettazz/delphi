import logging
import time

import pygame

from hotreload import Loader

if __name__ == "__main__":
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

  while True:
    new_weather = script.weather_updater(last_weather_check)
    if new_weather:
      last_weather_check = time.time()
      weather = new_weather
    script.run(screen, background, weather)
    time.sleep(1)