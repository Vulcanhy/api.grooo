__author__ = 'Vulcanhy & responsible'
# 总路由
from . import app
from .common.response import Response
from .Account.routes import Accounts
from .Shop.routes import Shops

# Flask-Restful路由
app.register_blueprint(Accounts, url_prefix='/api/v3/accounts')
app.register_blueprint(Shops, url_prefix='/api/v3/shops')


# 错误处理
@app.errorhandler(401)
def error401(error):
    return Response(code=401, message="权限验证失败", json=True)


@app.errorhandler(403)
def error403(error):
    return Response(code=403, message="没有权限", json=True)


@app.errorhandler(404)
def error404(error):
    return Response(code=404, message="资源不存在", json=True)


@app.errorhandler(405)
def error405(error):
    return Response(code=405, message="不支持此操作", json=True)

# @app.errorhandler(Exception)
# def error5xx(error):
#     return Response(code=500, message="服务器内部错误", json=True)
