import logging
import time
import traceback
from abc import ABC, abstractmethod

from config import Config
from drawingtools import DrawingTools as Draw

class Node(ABC):

  # default ttl (in seconds), now + TTL = new @expires
  DEFAULT_TTL = 900

  def __init__(self):
    self.logger = logging.getLogger('delphi')
    try:
      class_ttl = getattr(Config().ttl, type(self).__name__.lower())
    except AttributeError:
      class_ttl = None
    self.__ttl = class_ttl or self.DEFAULT_TTL
    self.failure_count = 0
    self.__expires = time.time()
    self.__cached_surface = None
    self.__data = None
    self.logger.debug('created new Node: %s' % type(self).__name__)

  @property
  def expires(self):
    # ttl for when this node's data is no longer valid and should be refreshed
    # time.time() based timestamp
    return self.__expires

  @property
  # return a screen sized pygame.Surface ready to be blitted onto the screen
  # if @expires has not passed, then return the cached previous Surface
  # if it has passed, call fetch() first then render a new Surface.
  # This is meant to be the only public interface to a Node
  def surface(self):
    if time.time() > self.expires:
      self.logger.debug('{%s} ttl has expired, fetching' % type(self).__name__)

      try:
        self.__fetch()

        self.failure_count = 0
        self.__expires = time.time() + self.__ttl
        self.logger.debug('{%s} fetch complete. new expiry %s' % (type(self).__name__, self.expires)) 

        self.__cached_surface = self.__draw()
        self.logger.debug('{%s} draw complete' % (type(self).__name__)) 
      except:
        self.failure_count = self.failure_count + 1
        self.__expires = time.time() + Config().ttl.failure.retry + (Config().ttl.failure.backoff * self.failure_count)
        if self.__cached_surface is None:
          self.__cached_surface = Draw.fake_screen()
        self.logger.error('{%s} fetch or draw failed (last %s times). using cached display. new expiry %s' % (type(self).__name__, self.failure_count, self.expires)) 
        self.logger.error(traceback.format_exc())

    self.logger.debug('{%s} ttl valid, returning cache' % type(self).__name__)
    return self.__cached_surface

  @abstractmethod
  # update internal data, implementation-specific
  # no return value
  def __fetch(self):
    raise NotImplementedError

  @abstractmethod
  # return a screen sized pygame.Surface ready to be blitted onto the
  # screen based on the current data, implementation-specific
  def __draw(self):
    raise NotImplementedError
