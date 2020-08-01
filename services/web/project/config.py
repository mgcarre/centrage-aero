import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY="zisizmyzob"
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static"
