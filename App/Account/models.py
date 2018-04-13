__author__ = 'Vulcanhy & responsible'
from flask.ext.security import UserMixin, RoleMixin
from passlib.handlers.django import django_pbkdf2_sha256
from datetime import datetime
from .. import db
from .. import cache

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')),
                       db.Index('uix_1', 'user_id', 'role_id', unique=True))


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), nullable=False)
    _building = db.relationship('School_Building', lazy='dynamic')

    @property
    def building(self):
        return School.query.get(self.id)._building.all()

    def get(self):
        return School.query.all()


class School_Building(db.Model):
    __table_args__ = (
        db.UniqueConstraint('school_id', 'name', name='uix_1'),
    )
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey(School.id))
    name = db.Column(db.String(20), nullable=False, index=True)


class Role(db.Model, RoleMixin):  # 权限表
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(11), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    push_id = db.Column(db.String(24), default='')
    email = db.Column(db.String(75), default='')
    nickname = db.Column(db.String(20), default=username)
    avatar = db.Column(db.String(255), default='')
    score = db.Column(db.Float, default=0)
    school_id = db.Column(db.Integer, db.ForeignKey(School.id))
    school = db.relationship('School')
    create_time = db.Column(db.DateTime, default=datetime.now())
    login_time = db.Column(db.DateTime)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('user', lazy='dynamic'))

    def __init__(self, id=None, username=None, password=None, school_id=None):
        self.id = id
        self.username = username
        self.nickname = '用户' + (username or '')[-4:]
        self.password = password
        self.school_id = school_id

    @classmethod
    def add(cls, username, password, school_id):
        user = User(username=username, password=django_pbkdf2_sha256.encrypt(password), school_id=school_id)
        db.session.add(user)
        db.session.commit()
        return user

    def get(self):
        if self.id:
            user = User.query.get(self.id)
        elif self.username:
            user = User.query.filter(User.username == self.username).first()
        return user

    def update(self, prof):
        user = User.query.get(self.id)
        user.email = prof.get("email", user.email)
        user.nickname = prof.get("nickname", user.nickname)
        user.avatar = prof.get("avatar", user.avatar)
        user.push_id = prof.get("push_id", user.push_id)
        db.session.commit()
        return True

    def enable(self):
        user = User.query.filter(User.username == self.username).first()
        user.active = True
        db.session.commit()
        return user

    def disable(self):
        user = User.query.filter(User.username == self.username).first()
        user.active = False
        db.session.commit()
        return user

    def changePassword(self, newPassword):
        user = User.query.filter(User.username == self.username).first()
        user.password = django_pbkdf2_sha256.encrypt(newPassword)
        db.session.commit()
        return True

    def getRank(self):
        @cache.cached(timeout=300, key_prefix='{}-{}-{}'.format(self.__class__, 'getRank', self.school_id))
        def cachedGetRank():
            users = User.query.filter(User.school_id == self.school_id, User.score > 0).order_by(-User.score).limit(
                30).all()
            return users

        return cachedGetRank()

    @classmethod
    def authenticate(cls, username, password):
        user = User.query.filter(User.username == username).first()
        if user:
            if user.active == False:
                return '您的账户已被禁用'
            if django_pbkdf2_sha256.verify(password, user.password):
                user.login_time = datetime.now()
                db.session.commit()
                return user
        return '用户名或密码错误'
