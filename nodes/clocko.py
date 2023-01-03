import time 

from .nodebase import Node
from drawingtools import DrawingTools as Draw

class Clocko(Node):

  def _Node__fetch(self):
    self.__data = {
      "time": time.strftime("%I:%M"),
      "date": time.strftime("%A, %B %-d")
    }

    if self.__data["time"][0] == "0":
      self.__data["time"] = self.__data["time"][1:]

  def _Node__draw(self):
    sf1 = Draw.header_shadowed(self.__data["time"], (242, 152), 210)
    sf2 = Draw.header_shadowed(self.__data["date"], (242, 252), 45)
    sf1.blit(sf2, (0, 0))

    return sf1

