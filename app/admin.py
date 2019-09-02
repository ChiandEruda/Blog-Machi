from flask_login import current_user
from flask import url_for
from flask import redirect
from flask import request
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView


class MyIndexView(AdminIndexView):
    
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        return current_user.username == 'admin'
 
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))


class MyBaseView(ModelView):

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        return current_user.username == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))


class MyUserView(MyBaseView):

    column_searchable_list=['username', 'email']

    column_labels = {
        'username' : '用户名',
        'email': '电子邮箱',
        'about_me': '简介'
    }

    column_list = ('username', 'email','about_me')


class MyPostView(MyBaseView):

    column_searchable_list=['title', 'body']

    column_labels = {
        'title' : '标题',
        'body': '正文',
        'author': '作者',
    }

    column_list = ('title', 'body','author')
    

class MyCommentView(MyBaseView):

    column_searchable_list=['body']

    column_labels = {
        'body' : '内容',
        'author': '作者',
        'post': '文章'
    }

    column_list = ('body', 'author','post')
