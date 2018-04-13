__author__ = 'Vulcanhy & responsible'
from flask.ext.restful import fields

output_shop = {
    "id": fields.Integer,
    "school_id": fields.Integer,
    "category": fields.String,
    "name": fields.String,
    "phone": fields.String,
    "logo": fields.String,
    "description": fields.String,
    "basePrice": fields.Float,
    "activity": fields.String,
    "rating": fields.Float(attribute=lambda shop: round(shop.rating, 2)),
    "rateNumber": fields.Integer,
    "monthSold": fields.Integer,
    "status": fields.Integer
}

output_full_shop = dict({
    "start_time": fields.String,
    "stop_time": fields.String,
    "weight": fields.Integer,
    "enable": fields.Boolean(attribute="active")
}, **output_shop)

output_shopItem = {
    "id": fields.Integer,
    "name": fields.String,
    "logo": fields.String,
    "category": fields.String,
    "price": fields.Float,
    "description": fields.String,
    "remain": fields.Integer,
    "monthSold": fields.Integer
}

output_shopRating = {
    "nickname": fields.String(attribute='user.nickname'),
    "logo": fields.String(attribute='user.avatar'),
    "rating": fields.Integer,
    "rating_remark": fields.String,
    "time": fields.String
}

output_orderItem = {
    "name": fields.String,
    "count": fields.Integer
}

output_order = {
    "order_id": fields.String,
    "seller": fields.Nested(output_shop),
    "username": fields.String(attribute='user.username'),
    "price": fields.Float,
    "detail": fields.Nested(output_orderItem),
    "building": fields.String,
    "address": fields.String,
    "remark": fields.String,
    "status": fields.Integer,
    "rating": fields.Integer,
    "rating_remark": fields.String,
    "time": fields.String
}

output_userProfile = {
    "building": fields.String,
    "address": fields.String,
}

output_userRank = {
    "id": fields.Integer,
    "username": fields.String,
    "nickname": fields.String,
    "avatar": fields.String,
    "score": fields.Float
}
