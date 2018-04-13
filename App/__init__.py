__author__ = 'Vulcanhy & responsible'
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore, Security
from flask.ext.cors import CORS
from flask.ext.cache import Cache
from . import config
from .common.http_method_override import HTTPMethodOverrideMiddleware

app = Flask(__name__)
app.config.from_object(config)
app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
db = SQLAlchemy(app)
CORS(app)
cache = Cache()
cache.init_app(app)

# Flask-Security
from .Account.models import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security().init_app(app, user_datastore, register_blueprint=False)
from .routes import app
