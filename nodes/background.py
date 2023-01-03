import os
import pygame
import random

from pygame.locals import *

from config import Config
from .nodebase import Node
from drawingtools import DrawingTools as Draw

class Background(Node):
  
  def _Node__fetch(self):
    backgrounds = [image for image in os.listdir(Config().path.background) if image.endswith(".jpg")]
    image_name = random.choice(backgrounds)
    image_path = "%s/%s" % (Config().path.background, image_name)
    img = pygame.image.load(image_path)
    self.logger.debug("loaded new background: %s" % image_path)

    img_width, img_height = img.get_size()
    if round(img_width / img_height, 3) > 0.6:
      new_height = Config().screen.height
      new_width = ((new_height * img_width) // img_height) + Config().screen.correction
    else:
      new_width = Config().screen.width + Config().screen.correction
      new_height = (new_width * img_height) // img_width

    background = pygame.transform.smoothscale(img, (new_width, new_height))
  
    width_offset = (Config().screen.width // 2) - (new_width // 2)
    height_offset = (Config().screen.height // 2) - (new_height // 2)

    self.logger.debug('new background: %s (%sx%s) offset (%s, %s)' % (image_name, new_width, new_height, width_offset, height_offset))

    self.__data = {
      "image": background,
      "offset": (width_offset, height_offset)
    }

  def _Node__draw(self):
    screen = Draw.fake_screen()
    screen.blit(self.__data['image'], (self.__data['offset'][0], self.__data['offset'][1]))

    return screen