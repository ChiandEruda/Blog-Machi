from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import ValidationError
from flask_ckeditor import CKEditorField

from app.models import User


class EditProfileForm(FlaskForm):
    about_me = TextAreaField('关于我', validators=[Length(min=0, max=140)])
    submit = SubmitField('提交')



class EditPostForm(FlaskForm):
    body = TextAreaField('', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('确认')


class PostForm(FlaskForm):
    title = StringField(
        '标题', validators=[DataRequired(), Length(min=0, max=20)])
    body = CKEditorField('正文', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('发布')


class SearchForm(FlaskForm):
    keyword = StringField('')
    submit = SubmitField('搜索')


class MessageForm(FlaskForm):
    message = TextAreaField('', validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('确认')


class CommentForm(FlaskForm):
    body = TextAreaField('评论', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('确认')
