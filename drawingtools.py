import fontawesome as fa
import pygame

from pygame.locals import *

from config import Config

class DrawingTools:
    
    DEFAULT_TEXT_COLOR = (255, 255, 255)

    @staticmethod
    def _get_fa_font(size):
        return pygame.font.Font('%s/fa-solid-900.ttf' % Config().path.font, size)

    @staticmethod
    def _get_text_font(size):
        return pygame.font.Font('%s/Staatliches-Regular.ttf' % Config().path.font, size)

    @staticmethod
    def fake_screen():
        size = width, height = Config().screen.width, Config().screen.height
        return pygame.Surface(size, pygame.SRCALPHA)

    @staticmethod
    def _textgen(text, position, size, color, align, font):
        text_obj = font.render(text, 1, color)
        textpos = text_obj.get_rect()
        if align == "left":
            textpos.topleft = position
        elif align == "right":
            textpos.topright = position
        else:
            textpos.center = position
        screen = DrawingTools.fake_screen()
        screen.blit(text_obj, textpos)
        return screen

    @staticmethod
    def header(text, position, size, color=DEFAULT_TEXT_COLOR, align="center"):
        font = DrawingTools._get_text_font(size)
        return DrawingTools._textgen(text, position, size, color, align, font)

    @staticmethod
    def header_shadowed(text, position, size, color=DEFAULT_TEXT_COLOR, align="center", shadow_color=(0, 0, 0)):
        bg = DrawingTools.header(text, position, size, shadow_color, align)
        fore = DrawingTools.header(text, (position[0] - 2, position[1] - 2), size, color, align)

        bg.blit(fore, (0, 0))
        return bg

    @staticmethod
    def body_text(text, position, size, color=DEFAULT_TEXT_COLOR, align="left"):
        font = DrawingTools._get_text_font(size)
        return DrawingTools._textgen(text, position, size, color, align, font)

    @staticmethod
    def body_text_shadowed(text, position, size, color=DEFAULT_TEXT_COLOR, align="left", shadow_color=(0, 0, 0)):
        bg = DrawingTools.body_text(text, position, size, shadow_color, align)
        fore = DrawingTools.body_text(text, (position[0] - 2, position[1] - 2), size, color, align)

        bg.blit(fore, (0, 0))
        return bg

    @staticmethod
    def fa_text(name, position, size, color=DEFAULT_TEXT_COLOR, align="center"):
        font = DrawingTools._get_fa_font(size)
        return DrawingTools._textgen(fa.icons[name], position, size, color, align, font)

    @staticmethod
    def fa_text_shadowed(name, position, size, color=DEFAULT_TEXT_COLOR, align="center", shadow_color=(0, 0, 0)):
        bg = DrawingTools.fa_text(name, position, size, shadow_color, align)
        fore = DrawingTools.fa_text(name, (position[0] - 2, position[1] - 2), size, color, align)

        bg.blit(fore, (0, 0))
        return bg

    @staticmethod
    def fullscreen_message(message, color):
        screen = DrawingTools.fake_screen()
        screen.fill((0, 0, 0))
        msg = DrawingTools.header(message, (240, 400), 30, color)
        screen.blit(msg, (0, 0))
        return screen

    @staticmethod
    def fa_prefixed_text(icon_name, text, position, size, color=DEFAULT_TEXT_COLOR, align="center"):
        FA_OFFSET_Y = -3
        FA_SPACING = 5

        fa_font = DrawingTools._get_fa_font(size)
        body_font = DrawingTools._get_text_font(size)

        fa_obj = fa_font.render(fa.icons[icon_name], 1, color)
        text_obj = body_font.render(text, 1, color)

        combo_surface = pygame.Surface((fa_obj.get_width() + FA_SPACING + text_obj.get_width(), fa_obj.get_height()), pygame.SRCALPHA)

        combo_surface.blit(fa_obj, (0, 0))
        combo_surface.blit(text_obj, (fa_obj.get_width() + FA_SPACING, FA_OFFSET_Y))

        da_rect = combo_surface.get_rect()

        if align == "left":
            da_rect.topleft = position
        elif align == "right":
            da_rect.topright = position
        else:
            da_rect.center = position

        screen = DrawingTools.fake_screen()
        screen.blit(combo_surface, da_rect)

        return screen

    @staticmethod
    def fa_prefixed_text_shadowed(icon_name, text, position, size, color=DEFAULT_TEXT_COLOR, align="center", shadow_color=(0, 0, 0)):
        bg = DrawingTools.fa_prefixed_text(icon_name, text, position, size, shadow_color, align)
        fore = DrawingTools.fa_prefixed_text(icon_name, text, (position[0] - 2, position[1] - 2), size, color, align)
        
        bg.blit(fore, (0, 0))
        return bg
