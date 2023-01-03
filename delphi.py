import importlib
import logging
import os
import signal
import sys
import time
from collections import OrderedDict
from pyfiglet import Figlet

import pygame
from pygame.locals import *

from config import Config
from drawingtools import DrawingTools as Draw

FULLSCREEN_MODE = 0

class Delphi:
  def __init__(self):
    self.logger = logging.getLogger(Config().logging.name)
    log_formatter = logging.Formatter(Config().logging.format)

    handler = logging.FileHandler(Config().logging.file)
    handler.setFormatter(log_formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(level=Config().logging.level)

    figl = Figlet(font='larry3d')
    banner = figl.renderText("hello delphi")
    self.logger.info("\n" + banner)

    signal.signal(signal.SIGINT, self.quitter)
    signal.signal(signal.SIGTERM, self.quitter)

    pygame.init()

    size = width, height = Config().screen.width, Config().screen.height
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

    # defines what nodes we will try to load and use
    # order matters! surfaces will be rendered onto the screen in this order
    self.nodes = OrderedDict([
      ("background", None), 
      ("clocko", None),
      # ("ambient", None),
      ("weather", None),
      # ("aqi", None),
      # ("calendar", None)
    ])

    self.alive = True

  def splash_screen(self):
    sf1 = Draw.fullscreen_message("hello, delphi", (0, 100, 255))
    sf2 = Draw.fa_text("hourglass-half", (Config().screen.width / 2, 450), 30, (0, 100, 255))
    self.screen.blit(sf1, (0, 0))
    self.screen.blit(sf2, (0, 0))
    pygame.display.flip()

  def draw_screen(self):
    # loop through nodes, get surfaces 
    # blit em all onto the screen
    for node_name, node in self.nodes.items():
      self.screen.blit(node.surface, (0, 0))

    pygame.display.flip()

  def runner(self):
    # import and init nodes based on dict definition above
    for node in self.nodes.keys():
      node_class = getattr(importlib.import_module("nodes.%s" % node), node.capitalize())
      self.nodes[node] = node_class()

    while self.alive:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.quitter(msg='pygame QUIT event')
        if event.type == KEYDOWN:
          if event.key == K_q:
            self.quitter(msg='Q key')
          if event.key == K_ESCAPE:
            self.quitter(msg='ESC key')
          # more key actions?

      self.draw_screen()

      time.sleep(1)

  def quitter(self, signum=None, frame=None, msg=None):
    if signum:
      self.logger.debug('caught signal %s, ending runloop' % signum)
    if msg:
      self.logger.debug('killed by %s, ending runloop' % msg)
    self.alive = False
    
    self.logger.info('goodbye!')

    # specific shutdown tasks for the gpio/dht tools
    if "ambient" in self.nodes.keys() and self.nodes["ambient"].DHT_SUPPORT:
      self.nodes["ambient"].dhtDevice = None
      GPIO.cleanup()

    pygame.display.quit()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
  d = Delphi()
  d.splash_screen()
  d.runner()