import time 

from .nodebase import Node
from drawingtools import DrawingTools as Draw

class Calendar(Node):

  def _Node__fetch(self):
    self.__data = {
      "time": time.strftime("%I:%M"),
      "date": time.strftime("%A, %B %-d")
    }

    if self.__data["time"][0] == "0":
      self.__data["time"] = self.__data["time"][1:]

  def _Node__draw(self):
    text_color = (255, 255, 255)

    # Draw.header_shadowed(self.screen, self.__data["time"], (242, 152), 210, text_color)
    # Draw.header_shadowed(self.screen, self.__data["date"], (242, 252), 45, text_color)