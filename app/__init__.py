import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
from flask_moment import Moment
from flask_msearch import Search
from flask_admin import Admin
from flask_babelex import Babel

from config import Config
from app.admin import MyIndexView
from app.admin import MyUserView
from app.admin import MyPostView
from app.admin import MyCommentView


bootstrap = Bootstrap()
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = '请从此页面登录.'
mail = Mail()
moment = Moment()
search = Search()
admin = Admin(name='后台管理', template_mode='bootstrap3', index_view=MyIndexView(template='admin/welcome.html'))
babel = Babel()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db) 
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    search.init_app(app)
    admin.init_app(app)
    babel.init_app(app)

    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    if app.config['MAIL_SERVER']:
        auth = None
        secure = None

        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        
        if app.config['MAIL_USE_TLS']:
            secure = ()

        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['ADMINS'],
            toaddrs=app.config['ADMINS'], 
            subject='博客发生错误',
            credentials=auth, 
            secure=secure)

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler) 

    if not app.debug:

        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler('logs/blog.log', maxBytes=10240, backupCount=10)

        log_format_1 = '%(asctime)s %(levelname)s: %(message)s\n'  
        log_format_2 = '[in %(pathname)s:%(lineno)d]\n'  

        file_handler.setFormatter(logging.Formatter(log_format_1+log_format_2))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Blog-Machi startup')   

    return app

from app import models

admin.add_view(MyUserView(models.User, db.session, name='用户管理'))
admin.add_view(MyPostView(models.Post, db.session, name='文章管理'))
admin.add_view(MyCommentView(models.Comment, db.session, name='评论管理'))