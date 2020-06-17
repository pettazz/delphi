import logging
import sys
import time
import os
import json
import random

import requests

import adafruit_dht
try:
    import board
except NotImplementedError:
    pass

import pygame
from pygame.locals import *

from statictools import * 

def weather_updater(last_weather_check):
    logger = logging.getLogger('weather_updater')
    logger.setLevel(logging.DEBUG)

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

def ambient_updater(last_ambient_check, dhtDevice):
    logger = logging.getLogger('ambient_updater')
    logger.setLevel(logging.DEBUG)

    ambient = None
    if time.time() - last_ambient_check > AMBIENT_INTERVAL:
        logger.info('refreshing ambient data...')
        try:
            tempf = dhtDevice.temperature * (9 / 5) + 32
            humidity = dhtDevice.humidity

            ambient = {
                "temperature": "{:.1f}".format(tempf),
                "humidity": humidity
            }
            logger.info("successfully fetched new ambient readings: %s" % ambient)
        except Exception as e:
            logger.warning("failed to fetch ambient, guess we'll try next tick")
            logger.warning(e)

    return ambient

def background_updater(last_background_update):
    logger = logging.getLogger('background_updater')
    logger.setLevel(logging.DEBUG)

    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800
    SCREEN_WIDTH_CORRECTION = 80 # the pixels are wrong? wat da fuk

    background_details = None

    if time.time() - last_background_update > BACKGROUND_INTERVAL:
        logger.info('updating background...')

        backgrounds = [image for image in os.listdir(BACKGROUND_PATH) if image.endswith(".jpg")]
        image_name = random.choice(backgrounds)
        img = pygame.image.load(BACKGROUND_PATH + image_name)

        img_width, img_height = img.get_size()
        if img_width < img_height:
            new_width = SCREEN_WIDTH + SCREEN_WIDTH_CORRECTION
            new_height = (new_width * img_height) // img_width
        else:
            new_height = SCREEN_HEIGHT
            new_width = ((new_height * img_width) // img_height) + SCREEN_WIDTH_CORRECTION

        background = pygame.transform.scale(img, (new_width, new_height))
      
        width_offset = (SCREEN_WIDTH // 2) - (new_width // 2)
        height_offset = (SCREEN_HEIGHT // 2) - (new_height // 2)

        background_details = {
            "image": background,
            "offset": (width_offset, height_offset)
        }

        logger.info('new background: %s (%sx%s) offset (%s, %s)' % (image_name, new_width, new_height, width_offset, height_offset))

    return background_details

def quit(reason="unknown"):
    logger = logging.getLogger('quit')
    logger.setLevel(logging.DEBUG)
    logger.info("killed by %s, goodbye!" % reason)
    sys.exit()

def run(screen, weather, ambient, background):
    logger = logging.getLogger('runloop')
    logger.setLevel(logging.DEBUG)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit('pygame QUIT event')
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                quit('ESC key')

    if background is not None:
        screen.blit(background['image'], (background['offset'][0], background['offset'][1]))

    now_time = time.strftime("%I:%M")
    now_date = time.strftime("%A, %B %-d")

    if now_time[0] == "0":
        now_time = now_time[1:]

    text_shadow(screen, now_time, (242, 202), 200, (255, 255, 255))
    text_shadow(screen, now_date, (242, 302), 45, (255, 255, 255))

    if ambient:
        fa_text_shadow(screen, 'tachometer-alt', (372, 472), 65, (255, 255, 255), "left")
        text_shadow(screen, "Temperature: %s°F" % ambient['temperature'], (52, 472), 30, (255, 255, 255), "left")
        text_shadow(screen, "Humidity: %s%%" % ambient['humidity'], (52, 502), 30, (255, 255, 255), "left")

    if weather:
        icon = WEATHER_ICON_MAP[weather['currently']['icon']]
        temp = int(weather['currently']['temperature'])
        feels = int(weather['currently']['apparentTemperature'])
        precipProb = int(weather['currently']['precipProbability'] * 100)
        hour_summary = weather['minutely']['summary']

        text1 = "%s°, feels like %s°, %s%% precip" % (temp, feels, precipProb)
        text2 = hour_summary

        fa_text_shadow(screen, icon, (32, 572), 65, (255, 255, 255), "left")
        text_shadow(screen, text1, (122, 572), 30, (255, 255, 255), "left")
        text_shadow(screen, text2, (122, 602), 30, (255, 255, 255), "left")

    pygame.display.flip()