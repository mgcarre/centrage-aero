# *_* coding: utf-8 *_*

"""Application configuration.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """App config
    """
    SECRET_KEY = "zisizmyzob"
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/prepavol/static"
