import logging
import sys
import time
import os
import json

import fontawesome as fa

import requests

import pygame
from pygame.locals import *

from statictools import * 

def weather_updater(last_weather_check):
    logger = logging.getLogger('weather_updater')

    weather = None
    if time.time() - last_weather_check > WEATHER_INTERVAL:
        logger.info('refreshing weather data...')
        try:
            res = requests.get(DARKSKY_FORECAST)
            if res.status_code == 200:
                weather = json.loads(res.text)
                logger.info("successfully fetched new weather, timestamp: %s" % weather['currently']['time'])
        except Exception as e:
            logger.warning("failed to fetch weather, guess we'll try next tick")
            logger.warning(e)

    return weather

def background_updater(last_background_update):
    logger = logging.getLogger('background_updater')

    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800

    background_details = None

    if time.time() - last_background_update > BACKGROUND_INTERVAL:
        logger.info('updating background...')
        img = pygame.image.load('assets/img/boston.jpg')
        img_width, img_height = img.get_size()
        if img_width < img_height:
            new_width = SCREEN_WIDTH
            new_height = (new_width * img_height) // img_width
        else:
            new_height = SCREEN_HEIGHT
            new_width = (new_height * img_width) // img_height

        background = pygame.transform.scale(img, (new_width, new_height))
      
        width_offset = (SCREEN_WIDTH // 2) - (new_width // 2)
        height_offset = (SCREEN_HEIGHT // 2) - (new_height // 2)

        background_details = {
            "image": background,
            "offset": (width_offset, height_offset)
        }

    return background_details

def run(screen, weather, background):
    logger = logging.getLogger('runloop')

    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                logger.info("killed by ESC key, goodbye!")
                sys.exit()

    if background is not None:
        screen.blit(background['image'], (background['offset'][0], background['offset'][1]))

    now_time = time.strftime("%I:%M")
    now_date = time.strftime("%A, %B %-d")

    if now_time[0] == "0":
        now_time = now_time[1:]

    text(screen, now_time, (242, 202), 200, (0, 0, 0))
    text(screen, now_time, (240, 200), 200, (255, 255, 255))

    text(screen, now_date, (242, 302), 30, (0, 0, 0))
    text(screen, now_date, (240, 300), 30, (255, 255, 255))

    if weather:
        icon = WEATHER_ICON_MAP[weather['currently']['icon']]
        temp = int(weather['currently']['temperature'])
        feels = int(weather['currently']['apparentTemperature'])
        precipProb = int(weather['currently']['precipProbability'] * 100)
        hour_summary = weather['minutely']['summary']

        text1 = "%s°, feels like %s°, %s%% precip" % (temp, feels, precipProb)
        text2 = hour_summary

        fa_text(screen, icon, (242, 602), 150, (0, 0, 0))
        fa_text(screen, icon, (240, 600), 150, (255, 255, 255))

        text(screen, text1, (242, 702), 30, (0, 0, 0))
        text(screen, text1, (240, 700), 30, (255, 255, 255))

        text(screen, text2, (242, 732), 30, (0, 0, 0))
        text(screen, text2, (240, 730), 30, (255, 255, 255))

    if os.path.isfile('/home/pi/src/clocko/hello'):
        fullscreen_message(screen, "Wow okay big man has an update for me", (138, 7, 7))

    pygame.display.flip()