import os

class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False