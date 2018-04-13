__author__ = 'Vulcanhy & responsible'
import os

# Flask
DEBUG = True

# Database
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = 'mysql://{0}:{1}@{2}:{3}/{4}'.format(os.environ['MYSQL_USERNAME'],
                                                               os.environ['MYSQL_PASSWORD'],
                                                               os.environ['MYSQL_PORT_3306_TCP_ADDR'],
                                                               os.environ['MYSQL_PORT_3306_TCP_PORT'],
                                                               os.environ['MYSQL_INSTANCE_NAME'])

# Flask-Security
SECRET_KEY = os.environ['SECRET_KEY']
SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authorization'
WTF_CSRF_ENABLED = False
SECURITY_TOKEN_MAX_AGE = 86400 * 15  # 秒

# Flask-Cache
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = os.environ['REDIS_PORT_6379_TCP_ADDR']
CACHE_REDIS_PORT = os.environ['REDIS_PORT_6379_TCP_PORT']
CACHE_REDIS_DB = ''
CACHE_REDIS_PASSWORD = os.environ['REDIS_PASSWORD']

#Qiniu
QINIU_ACCESS_KEY = os.environ['QINIU_ACCESS_KEY']
QINIU_SECRET_KEY = os.environ['QINIU_SECRET_KEY']