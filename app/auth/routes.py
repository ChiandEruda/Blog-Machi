from flask import render_template
from flask import request
from flask import flash
from flask import url_for
from flask import redirect
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from werkzeug.urls import url_parse
from flask import current_app

from app.auth.forms import LoginForm
from app.auth.forms import RegistrationForm
from app.auth import bp
from app.models import User
from app import db
from app.auth.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.auth.forms import ResetPasswordForm


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        capt = form.captcha.data
        if capt in current_app.config['CAPTCHA']:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('恭喜，您已注册成功！')
            return redirect(url_for('blog.index'))
        flash("验证码错误.")
        return redirect(url_for('auth.register'))
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码不正确.')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('blog.index')

        flash('{}已登录.'.format(form.username.data))
        return redirect(next_page)
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('blog.index'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('重置链接已发，请留意您的邮箱.')
            return redirect(url_for('auth.login'))
        flash('邮箱未注册.')
        return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password_request.html', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('blog.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('密码重置成功.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


