from flask import request
from flask import flash
from flask import redirect
from flask import url_for
from flask import render_template
from flask import current_app
from flask import g
from flask_login import login_required
from flask_login import current_user
from datetime import datetime

from app.blog import bp
from app import db
from app.models import User
from app.blog.forms import EditProfileForm
from app.blog.forms import EditPostForm
from app.blog.forms import PostForm
from app.blog.forms import SearchForm
from app.models import Post
from app.blog.forms import MessageForm
from app.models import Message
from app.blog.forms import CommentForm
from app.models import Comment


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('动态已发布！')
        return redirect(url_for('blog.index'))

    page = request.args.get('page', 1, type=int)
    per = current_app.config['POSTS_PER_PAGE']

    postz = current_user.stars_and_self_posts()
    posts = postz.paginate(page, per, False)

    next_url = url_for(
        'blog.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for(
        'blog.index', page=posts.prev_num) if posts.has_prev else None
    return render_template("blog/index.html", form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per = current_app.config['POSTS_PER_PAGE']

    postz = user.posts.order_by(Post.timestamp.desc())
    posts = postz.paginate(page, per, False)

    next_url = url_for('blog.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('blog.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('blog/user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
def explore():
    page = request.args.get('page', 1, type=int)
    per = current_app.config['POSTS_PER_PAGE']

    postz = Post.query.order_by(Post.timestamp.desc())
    posts = postz.paginate(page, per, False)

    next_url = url_for(
        'blog.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for(
        'blog.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('blog/index.html', posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('修改已保存.')
        return redirect(url_for('blog.user', username=current_user.username))
    form.about_me.data = current_user.about_me
    return render_template('blog/edit_profile.html', form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户 {} 不存在.'.format(username))
        return redirect(url_for('blog.index'))
    if user == current_user:
        flash('不能关注自己！')
        return redirect(url_for('blog.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('已成功关注 {}！'.format(username))
    return redirect(url_for('blog.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户 {} 不存在.'.format(username))
        return redirect(url_for('blog.index'))
    if user == current_user:
        flash('不能取消关注自己！')
        return redirect(url_for('blog.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('已取消关注 {}.'.format(username))
    return redirect(url_for('blog.user', username=username))


@bp.route('/search')
def search():
    keyword = request.args.get('keyword')
    if keyword:
        results = Post.query.msearch(keyword, fields=['title', 'body'], limit=20).all()
        return render_template('blog/search.html', results=results)
    return redirect(url_for('blog.index'))


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('blog/user_popup.html', user=user)


@bp.route('/post/<username>/<int:post_id>/delete')
@login_required
def delete_post(username, post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user==current_user and post_id:
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        db.session.delete(post)    
        db.session.commit()
    return redirect(url_for('blog.index'))


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                    body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('消息已发送.')
        return redirect(url_for('blog.user', username=recipient))
    return render_template('blog/send_message.html', form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    per = current_app.config['POSTS_PER_PAGE']
    messagez = current_user.messages_received.order_by(Message.timestamp.desc())
    messages = messagez.paginate(page, per, False)
    next_url = url_for('blog.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('blog.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('blog/messages.html', messages=messages.items,
                        next_url=next_url, prev_url=prev_url)


@bp.route('/edit/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = current_user.posts.filter_by(id=post_id).first_or_404()
    form = EditPostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash('修改已保存.')
        return redirect(url_for('blog.user', username=current_user.username))
    form.body.data = post.body
    return render_template('blog/edit_post.html', form=form)  


@bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    form = CommentForm()
    post = Post.query.filter_by(id=post_id).first_or_404()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('评论已发布！')
        return redirect(url_for('blog.post', post_id=post.id))

    page = request.args.get('page', 1, type=int)
    per = current_app.config['POSTS_PER_PAGE']

    comments = post.comments.paginate(page, per, False)

    next_url = url_for(
        'blog.post', page=comments.next_num, post_id=post.id) if comments.has_next else None
    prev_url = url_for(
        'blog.post', page=comments.prev_num, post_id=post.id) if comments.has_prev else None
    return render_template('blog/post.html', user=post.author, post=post, form=form, post_id=post.id, comments=comments.items, next_url=next_url, prev_url=prev_url, count=post.comments.count())






