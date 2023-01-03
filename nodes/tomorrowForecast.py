import time 

import requests

from .nodebase import Node
from drawingtools import DrawingTools as Draw

from assets.libstatic.tomorrow_demoweather import DEMODATA_FORECAST

class Forecast(Node):

  def _Node__fetch(self):
    now_dt = datetime.datetime.now()
    one_day_out_dt = now_dt + datetime.timedelta(days=1, hours=1)

    querystring = { "apikey": Config().key.tomorrowio }
    headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }
    payload = {
      "location": "%s, %s" % (Config().location.lat, Config().location.lon),
      "timezone": tzlocal.get_localzone_name(),
      "units": "imperial",
      "timesteps": ["5m"],
      "fields": [
        "temperature", 
        "temperatureApparent",
        "dewPoint",
        "windSpeed",
        "precipitationIntensity",
        "precipitationType",
        "visibility",
        "uvHealthConcern",
        "weatherCode",
        "epaHealthConcern"
      ],
      "endTime": one_day_out_dt.astimezone().replace(microsecond=0).isoformat()
    }
    if not USE_TESTDATA:
      response = requests.request("POST", 
        Config().api.tomorrowio.url, 
        json=payload, 
        headers=headers, 
        params=querystring)
      if response.status_code == 200:
        response_data = response.json()["data"]["timelines"]
        timeline = [tl for tl in response_data if tl["timestep"] == "5m"][0]
        fetchedWeatherData = timeline["intervals"][0]
      else:
        raise RuntimeError("invalid API response (%s): %s" % (response.status_code, response.text))
    else:
      fetchedWeatherData = DEMODATA_FORECAST


    self.__data = {}
    # iteration-based stuff
    # TODO: inflections
    hi = None
    lo = None

    for value in fetchedWeatherData:
      if hi is None or (value["values"]["temperature"] > hi["values"]["temperature"]):
        hi = value
      if lo is None or (value["values"]["temperature"] < lo["values"]["temperature"]):
        lo = value

    self.__data["hiValue"] = hi
    self.__data["loValue"] = lo


  def _Node__draw(self):
    pass