# *_* coding: utf-8 *_*

"""Application configuration.
"""

import os
from tempfile import mkdtemp

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """App base config"""

    DEBUG = False
    TESTING = False
    SECRET_KEY = "nonPROD"
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = mkdtemp()
    SESSION_PERMANENT = False
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/prepavol/static"


class DevelopmentConfig(Config):
    """App dev config"""

    DEBUG = True


class ProductionConfig(Config):
    """App prod config"""

    SECRET_KEY = "MeRgUeZ34"


class TestingConfig(Config):
    """App testing config"""

    TESTING = True
