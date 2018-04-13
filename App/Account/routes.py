__author__ = 'Vulcanhy & responsible'
from flask import Blueprint
from flask.ext.restful import Api
from .controller import Account, Token, Profile, Roles, Status, Schools, FileToken

Accounts = Blueprint('Accounts', __name__)
api = Api(Accounts, default_mediatype="application/json")
api.add_resource(Account, '/')
api.add_resource(Token, '/token')
api.add_resource(Profile, '/<int:userId>/profile')
api.add_resource(Roles, '/role')
api.add_resource(Status, '/status')
api.add_resource(Schools, '/school')
api.add_resource(FileToken, '/filetoken')
