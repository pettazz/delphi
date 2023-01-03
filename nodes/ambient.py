import time 

from .nodebase import Node
from drawingtools import DrawingTools as Draw

try:
  import board
  import RPi.GPIO as GPIO
  import adafruit_dht
  DHT_SUPPORT = True
except NotImplementedError:
  DHT_SUPPORT = False

class Ambient(Node):

  DHT_SUPPORT = DHT_SUPPORT

  def __init__(self):
    super().__init__()
    if DHT_SUPPORT:
      self.dhtDevice = adafruit_dht.DHT11(board.D27)

  def _Node__fetch(self):
    if DHT_SUPPORT:
      tempf = self.dhtDevice.temperature * (9 / 5) + 32
      humidity = self.dhtDevice.humidity

      self.__data = {
        "temperature": "{:.1f}".format(tempf),
        "humidity": humidity
      }
    else:
      self.__data = None

  def _Node__draw(self):
    if self.__data is not None:
      ambient_text = "%s° /  %s%%" % (self.__data['temperature'], self.__data['humidity'])
      return Draw.fa_prefixed_text_shadowed('microchip', ambient_text, (242, 730), 25)
    else:
      return Draw.fake_screen()