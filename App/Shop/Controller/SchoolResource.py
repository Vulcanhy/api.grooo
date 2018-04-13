__author__ = 'Vulcanhy & responsible'
from flask.ext.restful import Resource, reqparse, marshal
from flask.ext.security import auth_token_required, current_user
from datetime import datetime, timedelta
from .OutputFormat import output_order, output_userRank
from ..models import Shop_Seller, Shop_Orderlist, School, Shop_Config, User
from ...common.response import Response, HttpStatus


class SchoolResource:
    class Rank:
        class User(Resource):
            def get(self):
                '''
                获取用户排名
                :return:
                '''
                args = reqparse.RequestParser() \
                    .add_argument('school_id', type=int, location='args', required=True, help='学校id不能为空') \
                    .parse_args()
                users = User(school_id=args['school_id']).getRank()
                for user in users:
                    user.username = user.username[-4:]
                userRank = marshal(users, output_userRank)
                return Response(data=userRank)

        class Shop(Resource):
            def get(self):
                '''
                获取昨日前10销量商家排名
                :return:
                '''

    class Order(Resource):
        @auth_token_required
        def get(self):
            '''
            获取学校订单
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='args') \
                .add_argument('start_time', type=str, location='args', default=datetime.date(datetime.now())) \
                .add_argument('end_time', type=str, location='args',
                              default=datetime.date(datetime.now() + timedelta(days=1))) \
                .parse_args()
            args = dict(filter(lambda item: item[1] is not None, args.items()))
            if current_user.has_role('superadmin') or \
                    (current_user.has_role('admin') or current_user.has_role('shop_deliveryman')):
                orderList = Shop_Orderlist.query.filter(
                    Shop_Seller.school_id == args.get('school_id', current_user.school_id),
                    Shop_Orderlist.time.between(args['start_time'],
                                                args['end_time'])).all()
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="无权查看订单")
            orderList = marshal(orderList, output_order)
            return Response(data=orderList)

    class Announcement(Resource):
        def get(self):
            '''
            获取公告
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='args', required=True, help='学校id不能为空') \
                .parse_args()
            announcement = Shop_Config(school_id=args['school_id']).announcement
            return Response(data=announcement)

        @auth_token_required
        def put(self):
            """
            设置公告
            :return:
            """
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='json', required=True, help='学校id不能为空') \
                .add_argument('announcement', type=str, location='json', required=True, help='公告不能为空') \
                .parse_args()
            if current_user.has_role('superadmin') or (
                        current_user.has_role('admin') and current_user.school_id == args['school_id']):
                Shop_Config(school_id=args['school_id']).announcement = args['announcement']
                return Response(message='设置成功')
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    class Status(Resource):
        def get(self):
            '''
            获取学校状态
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='args', required=True, help='学校id不能为空') \
                .parse_args()
            config = {
                "status": Shop_Config(school_id=args['school_id']).status,
                "status_remark": Shop_Config(school_id=args['school_id']).status_remark
            }
            return Response(data=config)

        @auth_token_required
        def put(self):
            """
            设置学校状态
            :return:
            """
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='json', required=True, help='学校id不能为空') \
                .add_argument('status', type=int, location='json', required=True, help='状态不能为空') \
                .add_argument('status_remark', type=str, location='json', required=True, help='说明不能为空') \
                .parse_args()
            if current_user.has_role('superadmin') or (
                        current_user.has_role('admin') and current_user.school_id == args['school_id']):
                Shop_Config(school_id=args['school_id']).status = args['status']
                Shop_Config(school_id=args['school_id']).status_remark = args['status_remark']
                return Response(message='设置成功')
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    class Building(Resource):
        def get(self):
            args = reqparse.RequestParser() \
                .add_argument('school_id', type=int, location='args', required=True, help='学校id不能为空') \
                .parse_args()
            building = School(id=args['school_id']).building
            building = [item.name for item in building]
            return Response(data=building)
