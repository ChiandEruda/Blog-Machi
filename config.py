import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['549141930@qq.com']

    CAPTCHA = os.environ.get('CAPTCHA')

    POSTS_PER_PAGE = 5

    WHOOSH_BASE = os.path.join(basedir, '__msearch__')
    WHOOSH_ENABLE = True

    BABEL_DEFAULT_LOCALE = 'zh_CN'

    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_WIDTH = 500
