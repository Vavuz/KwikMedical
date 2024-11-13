import os

class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:password@hospital_db:5432/hospital_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False