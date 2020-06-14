import logging
import sys
import time
import os
import json

import fontawesome as fa

import requests

import pygame
from pygame import gfxdraw
from pygame.locals import *

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
    if script.has_changed():
      script.run(screen, background, last_weather_check, weather)

    time.sleep(1)