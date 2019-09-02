from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from wtforms.validators import Email
from wtforms.validators import EqualTo
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('用户名称', validators=[DataRequired()])
    email = StringField('注册邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('用户密码', validators=[DataRequired()])
    password2 = PasswordField(
        '确认密码', validators=[DataRequired(), EqualTo('password')])
    captcha = StringField('验证码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('此用户名已注册.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('此邮箱已注册.')


class LoginForm(FlaskForm):
    username = StringField('用户名称', validators=[DataRequired()])
    password = PasswordField('用户密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    submit = SubmitField('确认重置')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('重置密码', validators=[DataRequired()])
    password2 = PasswordField(
        '确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('确认重置')
