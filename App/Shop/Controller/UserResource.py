__author__ = 'Vulcanhy & responsible'
from flask.ext.restful import Resource, reqparse, marshal
from flask.ext.security import auth_token_required, current_user
from .OutputFormat import output_order, output_userProfile
from ..models import Shop_User, Shop_Orderlist
from ...common.response import Response, HttpStatus


class UserResource:
    class Order(Resource):
        @auth_token_required
        def get(self):
            '''
            获取个人订单
            :return:
            '''
            orderList = Shop_User(id=current_user.id).orderList
            if orderList:
                orderList = marshal(orderList, output_order)
                return Response(data=orderList)
            else:
                return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message="无符合条件的订单")

        @auth_token_required
        def post(self):
            '''
            评价个人订单
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('order_id', type=str, location='json', required=True, help='订单id不能为空') \
                .add_argument('rating', type=int, location='json', required=True, help='评分不能为空') \
                .add_argument('rating_remark', type=str, location='json') \
                .parse_args()
            if Shop_Orderlist(user_id=current_user.id, order_id=args['order_id']).rate(args['rating'],
                                                                                       args['rating_remark']):
                return Response(message='评价成功')
            else:
                return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='不能评价当前订单')

    class Profile(Resource):
        @auth_token_required
        def get(self):
            '''
            获取个人资料
            :return:
            '''
            profile = Shop_User(id=current_user.id).profile
            if profile:
                profile = marshal(profile, output_userProfile)
                return Response(data=profile)
            else:
                return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message="无资料")

        @auth_token_required
        def put(self):
            '''
            修改个人资料
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('building', type=str, location='json', required=True, help='楼栋地址不能为空') \
                .add_argument('address', type=str, location='json', required=True, help='具体地址不能为空') \
                .parse_args()
            Shop_User(id=current_user.id).profile = args
            return Response(message='修改成功')
