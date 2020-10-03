# *_* coding: utf-8 *_*

"""Application configuration."""

from datetime import timedelta
from dataclasses import dataclass
import pathlib
from tempfile import mkdtemp


@dataclass
class Config:
    """App base config."""

    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = "nonPROD"
    SESSION_TYPE: str = "filesystem"
    SESSION_FILE_DIR: str = mkdtemp()
    SESSION_PERMANENT: bool = True
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(hours=24)
    STATIC_FOLDER: str = pathlib.Path(__file__).parent.joinpath("static")


@dataclass
class DevelopmentConfig(Config):
    """App dev config."""

    DEBUG: bool = True


@dataclass
class ProductionConfig(Config):
    """App prod config."""

    SECRET_KEY: str = "MeRgUeZ34"


@dataclass
class TestingConfig(Config):
    """App testing config."""

    TESTING: bool = True
