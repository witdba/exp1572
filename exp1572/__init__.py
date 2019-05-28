from os import path
import gettext
import babel
import json

from exp1572 import dice, utils, settings, game
# import utils
# import settings
# from menu import getMenuChoice
from exp1572.menu import getMenuChoice
from importlib import reload

# does it later - after translation
# import common

# does it later - and if needed
# import glob

APP_NAME = 'exp1572'

here = path.abspath(path.dirname(__file__))
LOCALES_DIR = path.join(here, 'locales', '')

# MSG_LEVEL = 'DEBUG'
MSG_LEVEL = 'INFO'
languages = {}

