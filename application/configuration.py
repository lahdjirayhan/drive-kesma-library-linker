from decouple import config
from application.master import mastermind

class Configuration:
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MASTERMIND = mastermind
