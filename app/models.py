import jwt
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from flask import current_app
from hashlib import md5
from time import time

from app import db
from app import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


fansTable = db.Table('fans',
                     db.Column('fan_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('star_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    stars = db.relationship('User',
                            secondary=fansTable,
                            primaryjoin=(fansTable.c.fan_id == id),
                            secondaryjoin=(fansTable.c.star_id == id),
                            backref=db.backref('fans', lazy='dynamic'),
                            lazy='dynamic')

    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        messages = Message.query.filter_by(recipient=self)
        return messages.filter(Message.timestamp > last_read_time).count()

    def follow(self, user):
        if not self.is_following(user):
            self.stars.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.stars.remove(user)

    def is_following(self, user):
        return self.stars.filter(fansTable.c.star_id == user.id).count() > 0

    def stars_and_self_posts(self):
        all_posts = Post.query.join(
            fansTable, (fansTable.c.star_id == Post.user_id))
        stars_posts = all_posts.filter(fansTable.c.fan_id == self.id)
        self_posts = Post.query.filter_by(user_id=self.id)
        return stars_posts.union(self_posts).order_by(Post.timestamp.desc())

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=retro&s={}'.format(
            digest, size)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        payload = {'reset_password': self.id, 'exp': time() + expires_in}
        key = current_app.config['SECRET_KEY']
        return jwt.encode(payload, key, algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            key = current_app.config['SECRET_KEY']
            id = jwt.decode(token, key, algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Post(db.Model):
    __searchable__ = ['body', 'title']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Comment(db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = body = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)



    