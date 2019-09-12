from flask import render_template
from flask import request

from app import db
from app.errors import bp
from app.api.errors import error_response as api_error_response


# @app.errorhandler(404)
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    # 为了确保任何失败的数据库会话不会干扰模板触发的其他数据库访问
    # 执行会话回滚来将会话重置为干净的状态
    db.session.rollback()
    return render_template('errors/500.html'), 500


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.html'), 404
    

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500


