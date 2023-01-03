import datetime 
import time 

import requests

from .nodebase import Node
from config import Config
from drawingtools import DrawingTools as Draw
from assets.libstatic import pirate_weathermaps as weathermaps

from assets.libstatic.pirate_demoweather import DEMODATA

USE_TESTDATA = False

class Weather(Node):

  def _Node__fetch(self):
    ###############
    # Fetch Data

    qsData = { 
      "apiKey": Config().key.pirateweather,
      "lat": Config().location.lat, 
      "lon": Config().location.lon
    }
    headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }

    if not USE_TESTDATA:
      response = requests.request("GET", 
        Config().api.pirateweather.url % qsData, 
        headers=headers)
      if response.status_code == 200:
        fetchedWeatherData = response.json()
        # self.logger.debug(fetchedWeatherData)
      else:
        raise RuntimeError("invalid API response (%s): %s" % (response.status_code, response.text))
    else:
      fetchedWeatherData = DEMODATA

    ############### 
    # Parse Data
    self.__data = {}
    current_weather = fetchedWeatherData["currently"]
    minutely_weather = fetchedWeatherData["minutely"]
    hourly_weather = fetchedWeatherData["hourly"]
    today_weather = fetchedWeatherData["daily"]["data"][0]

    # times
    now_dt = datetime.datetime.now()
    sunrise_dt = datetime.datetime.fromtimestamp(today_weather["sunriseTime"])
    sunset_dt = datetime.datetime.fromtimestamp(today_weather["sunsetTime"])
    is_night = now_dt < sunrise_dt or now_dt > sunset_dt
    if is_night:
      sun_next = "rise"
      sun_dt = sunrise_dt
    else:
      sun_next = "set"
      sun_dt = sunset_dt

    sun_time = sun_dt.strftime("%I:%M")
    if sun_time[0] == "0":
      sun_time = sun_time[1:]

    self.__data["is_night"] = is_night
    self.__data["sun_next"] = sun_next
    self.__data["sun_time"] = sun_time

    # friendly view
    weather_type = weathermaps.WEATHER_MAP[current_weather["icon"]]
    self.__data["icon"] = weather_type["icon"]
    self.__data["weather_text"] = weather_type["text"]

    # temperature 
    self.__data["temp"] = temp = int(current_weather["temperature"])
    self.__data["feels_like"] = feels_like = int(current_weather["apparentTemperature"])

    change_symbol = "+" if feels_like > temp else "-"
    margin = abs(temp - feels_like)
    feels_like_indicator = ""
    if margin > 0:
      for interval in range(0, (margin // 5) + 1):
        feels_like_indicator = feels_like_indicator + change_symbol
      self.logger.debug("feels like margin of %s, displaying %s" % (margin, feels_like_indicator))
    self.__data["feels_like_indicator"] = feels_like_indicator

    # humidity 
    dewpoint = current_weather["dewPoint"]
    if dewpoint <= 55:
        humidity_feels = 'low'
    elif dewpoint < 65:
        humidity_feels = 'medium'
    else:
        humidity_feels = 'high'
    self.__data["humidity_feels"] = humidity_feels
    self.__data["humidity"] = int(current_weather["humidity"]) * 100

    # wind
    self.__data["wind_speed"] = int(current_weather['windSpeed'])
    bearing = current_weather['windBearing']
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
    self.__data["wind_direction"] = wind_direction

    # uv index
    uv_level = current_weather["uvIndex"]
    if uv_level <= 2:
      uv_text = "Low"
    elif uv_level <= 5:
      uv_text = "Moderate"
    elif uv_level <= 7:
      uv_text = "High"
    elif uv_level <= 10:
      uv_text = "Very High"
    else:
      uv_text = "Extreme"

    self.__data["uv_text"] = uv_text

  def _Node__draw(self):
    """
    data looks like this:
    {
      'is_night': True
      'sun_next': 'rise'
      'sun_time': '6:56'
      'icon': 'cloud'
      'weather_text': 'Cloudy'
      'temp': 73
      'feels_like': 73
      'humidity_feels': 'high'
      'humidity': 66
      'wind_speed': 2
      'wind_direction': 'SE'
      'aqi_level': 0
      'aqi_text': 'Good'
      'aqi_color': 'green'
      'uv_text': 'Low'
    }
    """
    items = []

    items.append(Draw.fa_text_shadowed(self.__data["icon"], (175, 507), 90))
    items.append(Draw.header_shadowed(str(self.__data["temp"]) + "°", (305, 510), 100))
    items.append(Draw.body_text_shadowed(self.__data["feels_like_indicator"], (340, 500), 35))

    base = Draw.fake_screen()
    for item in items:
      base.blit(item, (0,0))

    return base