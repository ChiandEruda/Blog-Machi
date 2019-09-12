import jwt
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from flask import current_app
from hashlib import md5
from time import time
from flask import url_for
import base64
from datetime import timedelta
import os

from app import db
from app import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


fansTable = db.Table('fans',
                     db.Column('fan_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('star_id', db.Integer, db.ForeignKey('user.id'))
                     )


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(db.Model, UserMixin, PaginatedAPIMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    likes = db.relationship('User',
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
            self.likes.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.likes.remove(user)

    def is_following(self, user):
        return self.likes.filter(fansTable.c.star_id == user.id).count() > 0

    def likes_and_self_posts(self):
        all_posts = Post.query.join(
            fansTable, (fansTable.c.star_id == Post.user_id))
        likes_posts = all_posts.filter(fansTable.c.fan_id == self.id)
        self_posts = Post.query.filter_by(user_id=self.id)
        return likes_posts.union(self_posts).order_by(Post.timestamp.desc())

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

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'fans_count': self.fans.count(),
            'likes_count': self.likes.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'fans': url_for('api.get_fans', id=self.id),
                'likes': url_for('api.get_likes', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])        

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

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




    