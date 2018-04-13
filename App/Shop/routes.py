__author__ = 'Vulcanhy & responsible'
from flask import Blueprint
from flask.ext.restful import Api
from .Controller import ShopResource, UserResource, SchoolResource

Shops = Blueprint('Shops', __name__)
api = Api(Shops, default_mediatype="application/json")
api.add_resource(ShopResource.Shop, '/shop')
api.add_resource(ShopResource.Info, '/shop/<int:shopId>/info')
api.add_resource(ShopResource.Rating, '/shop/<int:shopId>/rating')
api.add_resource(ShopResource.Menu, '/shop/<int:shopId>/menu')
api.add_resource(ShopResource.Order, '/shop/<int:shopId>/order', endpoint='Shop_Order')
api.add_resource(ShopResource.Status, '/shop/<int:shopId>/status')
api.add_resource(UserResource.Order, '/user/order', endpoint='User_Order')
api.add_resource(UserResource.Profile, '/user/profile')
api.add_resource(SchoolResource.Rank.User, '/rank/user')
api.add_resource(SchoolResource.Order, '/order', endpoint='School_Order')
api.add_resource(SchoolResource.Announcement, '/announcement')
api.add_resource(SchoolResource.Status, '/status', endpoint='School_Status')
api.add_resource(SchoolResource.Building, '/building')
