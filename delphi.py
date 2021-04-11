import logging
import time, datetime
import pathlib
import signal
import sys
import os
import json
import random
import copy

import requests
from requests.exceptions import RequestException
from tzlocal import get_localzone
from ics import Calendar, Event

import pygame
from pygame.locals import *

from pyfiglet import Figlet

try:
    import board
    import RPi.GPIO as GPIO
    import adafruit_dht
    DHT_SUPPORT = True
except NotImplementedError:
    DHT_SUPPORT = False

from statictools import * 

FULLSCREEN_MODE = 0

class Delphi:
  def __init__(self):
    self.logger = logging.getLogger('delphi')
    log_formatter = logging.Formatter("%(asctime)s %(name)s.%(funcName)s [%(levelname)s] %(message)s")

    handler = logging.FileHandler('clocko.log')
    handler.setFormatter(log_formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(level=LOGLEVEL)

    figl = Figlet(font='larry3d')
    banner = figl.renderText("hello delphi")
    self.logger.info("\n" + banner)

    signal.signal(signal.SIGINT, self.quitter)
    signal.signal(signal.SIGTERM, self.quitter)

    pygame.init()

    size = width, height = 480, 800
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

    self.last_weather_forecast_check = 0
    self.last_weather_realtime_check = 0
    self.last_background_update = 0
    self.last_calendar_update = 0
    if DHT_SUPPORT:
      self.dhtDevice = adafruit_dht.DHT11(board.D27)
      self.last_ambient_check = 0

    self.alive = True

  def weather_updater(self):
    weather = None
    forecast_state = None
    realtime_check = False
    forecast_check = False

    if time.time() - self.last_weather_realtime_check > WEATHER_INTERVAL_REALTIME:
        self.logger.info('refreshing weather realtime data...')
        try:
            res = requests.get(CLIMACELL_REALTIME, timeout=1, params=CLIMACELL_PARAMS)
            if res.status_code == 200:
                weather_raw = json.loads(res.text)

                # basics
                now_dt = datetime.datetime.now(tz=get_localzone())
                sunrise_dt = datetime.datetime.fromisoformat(weather_raw['sunrise']['value'].replace('Z', '+00:00')).astimezone(get_localzone())
                sunset_dt = datetime.datetime.fromisoformat(weather_raw['sunset']['value'].replace('Z', '+00:00')).astimezone(get_localzone())
                is_night = now_dt < sunrise_dt or now_dt > sunset_dt 

                icon = WEATHER_ICONS_MAP['day' if not is_night else 'night'][weather_raw['weather_code']['value']]

                # temp/feels like
                temp = int(weather_raw['temp']['value'])
                feels_like = int(weather_raw['feels_like']['value'])

                change_symbol = "+" if feels_like > temp else "-"
                margin = abs(temp - feels_like)
                feels_like_indicator = ""
                if margin > 0:
                    for interval in range(0, (margin // 5) + 1):
                        feels_like_indicator = feels_like_indicator + change_symbol

                self.logger.debug("feels like margin of %s, displaying %s" % (margin, feels_like_indicator))

                # high/low, is this even in the api?
                high = 90 #int(weather_raw['weather_code']['value'])
                low = 70 #int(weather_raw['weather_code']['value'])

                # humidity
                dewpoint = int(weather_raw['dewpoint']['value'])
                if dewpoint <= 55:
                    humidity = 'low'
                elif dewpoint < 65:
                    humidity = 'medium'
                else:
                    humidity = 'high'

                if is_night:
                    sun_next = 'rise'
                    sun_time_iso = weather_raw['sunrise']['value']
                else:
                    sun_next = 'set'
                    sun_time_iso = weather_raw['sunset']['value']
                sun_dt = datetime.datetime.fromisoformat(sun_time_iso.replace('Z', '+00:00')).astimezone(get_localzone())
                sun_time = sun_dt.strftime("%I:%M")

                if sun_time[0] == "0":
                    sun_time = sun_time[1:]

                # wind
                wind_speed = int(weather_raw['wind_speed']['value'])
                bearing = weather_raw['wind_direction']['value']
                if bearing > 348.75 or bearing <= 33.75:
                    wind_direction = 'N'
                elif bearing > 33.75 and bearing <= 78.75:
                    wind_direction = 'NE'
                elif bearing > 78.75 and bearing <= 123.75:
                    wind_direction = 'E'
                elif bearing > 123.75 and bearing <= 168.75:
                    wind_direction = 'SE'
                elif bearing > 168.75 and bearing <= 213.75:
                    wind_direction = 'S'
                elif bearing > 213.75 and bearing <= 258.75:
                    wind_direction = 'SW'
                elif bearing > 258.75 and bearing <= 303.75:
                    wind_direction = 'W'
                elif bearing > 303.75 and bearing <= 348.75:
                    wind_direction = 'NW'

                # air quality
                aqi = weather_raw['epa_aqi']['value']
                if aqi <= 50:
                    air_quality = 'good'
                    air_quality_color = 'green'
                elif aqi <= 100:
                    air_quality = 'moderate'
                    air_quality_color = 'yellow'
                elif aqi <= 150:
                    air_quality = 'bad'
                    air_quality_color = 'orange'
                elif aqi <= 200:
                    air_quality = 'unhealthy'
                    air_quality_color = 'red'
                elif aqi <= 300:
                    air_quality = 'very unhealthy'
                    air_quality_color = 'purple'
                else:
                    air_quality = 'hazardous'
                    air_quality_color = 'maroon'
                
                # pollen
                tree_pollen = weather_raw['pollen_tree']['value']
                tree_pollen = round(tree_pollen) if tree_pollen is not None else 0
                tree_pollen_color = POLLEN_COLOR_SCALE[tree_pollen]

                weed_pollen = weather_raw['pollen_weed']['value']
                weed_pollen = round(weed_pollen) if weed_pollen is not None else 0
                weed_pollen_color = POLLEN_COLOR_SCALE[weed_pollen]

                grass_pollen = weather_raw['pollen_grass']['value']
                grass_pollen = round(grass_pollen) if grass_pollen is not None else 0
                grass_pollen_color = POLLEN_COLOR_SCALE[grass_pollen]

                # for use in generating forecast state in nowcast
                current_state = weather_raw['weather_code']['value']

                realtime_check = True

                self.logger.info("successfully fetched new weather realtime, current time: %s" % weather_raw['observation_time']['value'])
            else:
                raise RequestException("API response: %s: %s" % (res.status_code, res.text))
        except Exception as e:
            self.logger.warning("failed to fetch weather realtime, guess we'll try next time", exc_info=True)

        # even if it fails, we cant retry every tick or climacell will be mad 
        # at us for going over the rate limit by 900% again
        self.last_weather_realtime_check = time.time()

    if time.time() - self.last_weather_forecast_check > WEATHER_INTERVAL_FORECAST:
        self.logger.info('refreshing weather forecast data...')
        try:
            one_hour_out = (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
            params = copy.deepcopy(CLIMACELL_PARAMS)
            params['end_time'] = one_hour_out
            params['timestep'] = 5
            params['fields'] = 'weather_code'
            res = requests.get(CLIMACELL_NOWCAST, timeout=1, params=params)
            if res.status_code == 200:
                weather_raw = json.loads(res.text)

                # next hour status 
                if realtime_check:
                    current = current_state
                elif self.weather is not None:
                    current = self.weather['current_state']
                else:
                    current = weather_raw[0]['weather_code']['value']
                inflections = []
                prev = current
                base_time = datetime.datetime.fromisoformat(weather_raw[0]['observation_time']['value'].replace('Z', '+00:00'))
                for idx, interval in enumerate(weather_raw):
                    if idx > 0 and not interval['weather_code']['value'] == prev:
                        compare_time = datetime.datetime.fromisoformat(interval['observation_time']['value'].replace('Z', '+00:00'))
                        diff_time = compare_time - base_time
                        inflections.append({
                            'code': interval['weather_code']['value'],
                            'mins_from_prev': diff_time.seconds // 60
                        })
                        prev = interval['weather_code']['value']
                        base_time = compare_time

                if inflections:
                    # clear for 20 mins, then mostly clear for 20 mins, then mostly clear for 20 mins, then mostly clear
                    forecast_state = "%s" % WEATHER_CODES_TEXT[current]
                    for inflection in inflections:
                        if int(inflection['mins_from_prev']) > 0:
                            forecast_state = forecast_state + " for %s mins, then %s" % (inflection['mins_from_prev'], WEATHER_CODES_TEXT[inflection['code']])
                        else:
                            forecast_state = forecast_state + ", then %s" % WEATHER_CODES_TEXT[inflection['code']]
                else:
                    forecast_state = "%s for the hour" % WEATHER_CODES_TEXT[current]

                forecast_check = True

                self.logger.info("successfully fetched new weather forecast, current time: %s" % weather_raw[0]['observation_time']['value'])
            else:
                raise RequestException("API response: %s: %s" % (res.status_code, res.text))
        except Exception as e:
            self.logger.warning("failed to fetch weather forecast, guess we'll try next time", exc_info=True)

        self.last_weather_forecast_check = time.time()

    if realtime_check:
        weather = {
            'temp': temp,
            'is_night': is_night,
            'icon': icon,
            'feels_like': feels_like,
            'feels_like_indicator': feels_like_indicator,
            'current_state': current_state,
            'high': high,
            'low': low,
            'dewpoint': dewpoint,
            'humidity': humidity,
            'sun_time': sun_time,
            'sun_next': sun_next,
            'wind_speed': wind_speed,   
            'wind_direction': wind_direction,
            'air_quality': air_quality,
            'air_quality_color': air_quality_color,
            'tree_pollen_color': tree_pollen_color,
            'weed_pollen_color': weed_pollen_color,
            'grass_pollen_color': grass_pollen_color
        }
    else:
        weather = self.weather

    if forecast_check:
        weather['state'] = forecast_state
    else:
        weather['state'] = self.weather['state'] if self.weather else current_state

    return weather

  def ambient_updater(self):
    ambient = None

    if DHT_SUPPORT:
      if time.time() - self.last_ambient_check > AMBIENT_INTERVAL:
          self.logger.info('refreshing ambient data...')
          try:
              tempf = self.dhtDevice.temperature * (9 / 5) + 32
              humidity = self.dhtDevice.humidity

              ambient = {
                  "temperature": "{:.1f}".format(tempf),
                  "humidity": humidity
              }
              self.last_ambient_check = time.time()

              self.logger.info("got new ambient, set last check time to %s" % self.last_ambient_check)
              self.logger.info("successfully fetched new ambient readings: %s" % ambient)
          except Exception as e:
              self.logger.warning("failed to fetch ambient, guess we'll try next tick")
              self.logger.warning(e)
    else:

      ambient = {
          "temperature": "{:.1f}".format(80),
          "humidity": "27"
      }
      self.logger.info("DHT support disabled, using fake data")

    return ambient

  def calendar_updater(self):
    events = None
    if time.time() - self.last_calendar_update > CALENDAR_INTERVAL:
        self.logger.info('updating calendars...')
        events = []

        try:
            for cal in CALENDARS:
                found_events = None
                if cal['day'] == 'tomorrow':
                    found_events = get_calendar_events_tomorrow(cal['url'])
                else:
                    found_events = get_calendar_events_today(cal['url'])

                for ev in found_events:
                    events.append({
                        'type': cal['type'],
                        'title': ev + (" Tomorrow" if cal['day'] == 'tomorrow' else "")
                    })

            self.last_calendar_update = time.time()

            self.logger.info("got new calendar events, set last check time to %s" % self.last_calendar_update)
        except Exception as e:
            self.logger.warning("failed to update calendars, guess we'll try next tick")
            self.logger.warning(e)

    return events

  def background_updater(self):
    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800
    SCREEN_WIDTH_CORRECTION = 80 # the pixels are wrong? wat da fuk

    background_details = None

    if time.time() - self.last_background_update > BACKGROUND_INTERVAL:
        self.logger.info('updating background...')

        backgrounds = [image for image in os.listdir(BACKGROUND_PATH) if image.endswith(".jpg")]
        image_name = random.choice(backgrounds)
        img = pygame.image.load(BACKGROUND_PATH + image_name)

        img_width, img_height = img.get_size()
        if round(img_width / img_height, 3) > 0.6:
            new_height = SCREEN_HEIGHT
            new_width = ((new_height * img_width) // img_height) + SCREEN_WIDTH_CORRECTION
        else:
            new_width = SCREEN_WIDTH + SCREEN_WIDTH_CORRECTION
            new_height = (new_width * img_height) // img_width

        background = pygame.transform.smoothscale(img, (new_width, new_height))
      
        width_offset = (SCREEN_WIDTH // 2) - (new_width // 2)
        height_offset = (SCREEN_HEIGHT // 2) - (new_height // 2)

        background_details = {
            "image": background,
            "offset": (width_offset, height_offset)
        }
        self.last_background_update = time.time()
        
        self.logger.info("updating background at %s" % self.last_background_update)
        self.logger.info('new background: %s (%sx%s) offset (%s, %s)' % (image_name, new_width, new_height, width_offset, height_offset))

    return background_details

  def draw_screen(self):
    text_color = (255, 255, 255)
    if self.background_details is not None:
        self.screen.blit(self.background_details['image'], (self.background_details['offset'][0], self.background_details['offset'][1]))

    now_time = time.strftime("%I:%M")
    now_date = time.strftime("%A, %B %-d")

    if now_time[0] == "0":
        now_time = now_time[1:]

    header_shadowed(self.screen, now_time, (242, 152), 210, text_color)
    header_shadowed(self.screen, now_date, (242, 252), 45, text_color)

    if self.events is not None:
        ypos = 300
        for event in self.events:
            fa_prefixed_text_shadowed(self.screen, EVENTS_TYPE_FA_ICONS[event['type']], event['title'], (240, ypos), 25, text_color)
            ypos = ypos + 30

    if self.weather is not None:
        weather = self.weather
        # main
        fa_text_shadowed(self.screen, weather['icon'], (175, 507), 90, text_color)
        header_shadowed(self.screen, str(weather['temp']) + "°", (305, 510), 100, text_color)
        body_text_shadowed(self.screen, weather['feels_like_indicator'], (340, 500), 35, text_color)
        state = weather['state']
        if len(state) > 30:
            split_pos = state.find(' ', 50) + 1
            if split_pos > 1:
                line1 = state[:split_pos]
                line2 = state[split_pos:]
                header_shadowed(self.screen, line1, (242, 570), 20, text_color)
                header_shadowed(self.screen, line2, (242, 590), 20, text_color)
            else:
                header_shadowed(self.screen, state, (242, 575), 23, text_color)
        else:
            header_shadowed(self.screen, state, (242, 575), 35, text_color)

        # hi/low
        fa_text_shadowed(self.screen, 'angle-up', (120, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['high']) + "°", (137, 600), 25, text_color)
        fa_text_shadowed(self.screen, 'angle-down', (190, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['low']) + "°", (207, 600), 25, text_color)

        # dewpoint
        fa_text_shadowed(self.screen, 'tint', (280, 603), 23, text_color, "left")
        body_text_shadowed(self.screen, str(weather['dewpoint']) + "°", (305, 600), 25, text_color)
        if weather['humidity'] == 'low':
            humidity_icon = 'smile'
        elif weather['humidity'] == 'medium':
            humidity_icon = 'meh'
        elif weather['humidity'] == 'high':
            humidity_icon = 'frown-open'
        fa_text_shadowed(self.screen, humidity_icon, (345, 603), 23, text_color, "left")

        # sunrise/set
        if weather['sun_next'] == 'rise':
            sun_icon = 'sun'
        else:
            sun_icon = 'moon'
        fa_text_shadowed(self.screen, sun_icon, (120, 640), 20, text_color, "left")
        body_text_shadowed(self.screen, weather['sun_time'], (145, 635), 25, text_color)

        # wind
        fa_text_shadowed(self.screen, 'wind', (260, 640), 20, text_color, "left")
        body_text_shadowed(self.screen, str(weather['wind_speed']), (293, 650), 25, text_color, "center")
        body_text_shadowed(self.screen, " mph", (303, 641), 17, text_color)
        body_text_shadowed(self.screen, str(weather['wind_direction']), (340, 635), 25, text_color) # an icon someday

        # pollen / aqi
        fa_text_shadowed(self.screen, 'tree', (120, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (137, 680), 20, COLOR_RGB[weather['tree_pollen_color']], "left")
        fa_text_shadowed(self.screen, 'leaf', (170, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (197, 680), 20, COLOR_RGB[weather['weed_pollen_color']], "left")
        fa_text_shadowed(self.screen, 'seedling', (230, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (253, 680), 20, COLOR_RGB[weather['grass_pollen_color']], "left")

        # aqi
        fa_text_shadowed(self.screen, 'industry', (324, 680), 20, text_color, "left")
        fa_text_shadowed(self.screen, 'dot-circle', (347, 680), 20, COLOR_RGB[weather['air_quality_color']], "left")

    if self.ambient is not None:
        fa_text_shadowed(self.screen, 'microchip', (170, 733), 20, text_color, "left")
        body_text_shadowed(self.screen, "%s° /  %s%%" % (self.ambient['temperature'], self.ambient['humidity']), (200, 730), 25, text_color)
        
    pygame.display.flip()

  def runner(self):
    self.weather = None
    self.ambient = None
    self.background_details = None
    self.events = None

    while self.alive:
      for event in pygame.event.get():
          if event.type == pygame.QUIT:
              self.quitter(msg='pygame QUIT event')
          if event.type == KEYDOWN:
              if event.key == K_ESCAPE:
                  self.quitter(msg='ESC key')
              if event.key == K_RIGHT:
                  self.last_background_update = 0
                  self.logger.info('next background...')

      new_weather = self.weather_updater()
      if new_weather is not None:
        self.weather = new_weather

      new_events = self.calendar_updater()
      if new_events is not None:
        self.events = new_events
      
      new_ambient = self.ambient_updater()
      if new_ambient is not None:
          self.ambient = new_ambient
          
      new_bg = self.background_updater()
      if new_bg is not None:
        self.background_details = new_bg

      self.draw_screen()

      time.sleep(1)

  def quitter(self, signum=None, frame=None, msg=None):
    if signum:
      self.logger.info('caught signal %s, ending runloop' % signum)
    if msg:
      self.logger.info('killed by %s, ending runloop' % msg)
    self.alive = False
    
    self.logger.info('goodbye!')
    self.dhtDevice = None
    GPIO.cleanup()
    pygame.display.quit()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
  d = Delphi()
  d.runner()