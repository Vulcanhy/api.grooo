from functools import wraps

__author__ = 'responsible'
from flask.ext.restful import Resource, reqparse, marshal
from flask.ext.security import auth_token_required, current_user, roles_required, roles_accepted
from sqlalchemy import exc
from datetime import datetime, timedelta
from .OutputFormat import *
from ..models import Shop_Seller, Shop_Orderlist, Shop_Itemlist, User, Shop_Config
from ...common.response import Response, HttpStatus
from ...common.jpush import jpush_msg


class ShopResource:
    class Shop(Resource):
        def get(self):
            """
            根据学校id和商店类别返回符合条件的所有商家或一个随机商家
            :return:
            """
            args = reqparse.RequestParser() \
                .add_argument('random', type=bool, location='args') \
                .add_argument('school_id', type=int, location='args', required=True, help='学校id不能为空') \
                .add_argument('fullinfo', type=bool, location='args', required=False, default=False) \
                .parse_args()
            if args.get("fullinfo", False):
                seller = Shop_Seller(school_id=args['school_id']).get(rand=args.get('random', False),
                                                                      includeDisabledSeller=True)
                seller = [marshal(item, output_full_shop) for item in seller]
            else:
                seller = Shop_Seller(school_id=args['school_id']).get(rand=args.get('random', False))
                seller = [marshal(item, output_shop) for item in seller]
            if seller:
                return Response(data=seller)
            else:
                return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message="无符合条件的商家")

        @auth_token_required
        def post(self):
            '''
            添加商家
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('username', type=str, location='json', required=True) \
                .add_argument('category', type=str, location='json', required=True) \
                .add_argument('name', type=str, location='json', required=True) \
                .add_argument('phone', type=str, location='json', required=True) \
                .add_argument('logo', type=str, location='json') \
                .add_argument('description', type=str, location='json') \
                .add_argument('basePrice', type=str, location='json', required=True) \
                .add_argument('activity', type=str, location='json') \
                .add_argument('start_time', type=str, location='json', required=True) \
                .add_argument('stop_time', type=str, location='json', required=True) \
                .add_argument('weight', type=str, location='json') \
                .parse_args()
            user = User(username=args['username']).get()
            if current_user.has_role('superadmin') or \
                    (current_user.school_id == user.school_id and (
                                current_user.has_role('admin') or current_user.has_role('shop_admin'))):
                args['id'] = user.id
                args['school_id'] = user.school_id
                del args['username']
                Shop_Seller.add(**args)
                return Response(message='添加成功')
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    class Info(Resource):
        def get(self, shopId):
            """
            根据商家id获取商家信息
            :param shopId:
            :return:
            """
            seller = Shop_Seller(id=shopId).get()
            if seller:
                seller = marshal(seller, output_shop)
                return Response(data=seller)
            else:
                return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message="无符合条件的商家")

        @auth_token_required
        def patch(self, shopId):
            '''
            修改商家信息
            :return:
            '''
            seller = Shop_Seller(id=shopId).get()
            if current_user.has_role('superadmin') or \
                    (current_user.school_id == seller.school_id and (
                                    current_user.has_role('admin') or current_user.has_role(
                                    'shop_admin') or current_user.has_role('shop_seller'))):
                args = reqparse.RequestParser() \
                    .add_argument('name', type=str, location='json') \
                    .add_argument('phone', type=str, location='json') \
                    .add_argument('logo', type=str, location='json') \
                    .add_argument('description', type=str, location='json') \
                    .add_argument('basePrice', type=float, location='json') \
                    .add_argument('activity', type=str, location='json') \
                    .add_argument('start_time', type=str, location='json') \
                    .add_argument('stop_time', type=str, location='json') \
                    .add_argument('weight', type=int, location='json') \
                    .add_argument('active', type=bool, location='json') \
                    .parse_args()
                args = dict(filter(lambda item: item[1] is not None, args.items()))
                if Shop_Seller(id=shopId).update(**args):
                    return Response(message='修改成功')
                else:
                    return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='修改失败')
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="没有权限")

    class Rating(Resource):
        def get(self, shopId):
            order = Shop_Seller(id=shopId).ratingList
            order = marshal(order, output_shopRating)
            return Response(message='获取成功', data=order)

    class Menu(Resource):
        def get(self, shopId):
            '''
            获取商家商品列表
            :return:
            '''
            seller = Shop_Seller(id=shopId).get()
            if seller:
                itemList = Shop_Seller(id=shopId).get().itemList
                itemList = [marshal(item, output_shopItem) for item in itemList]
                return Response(data=itemList)
            else:
                return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message="无符合条件的商家")

        @auth_token_required
        def post(self, shopId):
            '''
            添加商品
            :param shopId:
            :return:
            '''
            if not current_user.has_role('shop_seller') and current_user.id != shopId:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="没有权限")
            args = reqparse.RequestParser() \
                .add_argument('name', type=str, location='json', required=True, help='商品名不能为空') \
                .add_argument('logo', type=str, location='json') \
                .add_argument('category', type=str, location='json', required=True, help='商品类别不能为空') \
                .add_argument('price', type=float, location='json', required=True, help='商品价格不能为空') \
                .add_argument('description', type=str, location='json') \
                .add_argument('remain', type=int, location='json') \
                .parse_args()
            args['seller_id'] = current_user.id
            try:
                Shop_Itemlist.add(**args)
                return Response(code=HttpStatus.HTTP_201_CREATED, message='添加成功')
            except exc.IntegrityError:
                return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='添加失败,商品重复')

        @auth_token_required
        def put(self, shopId):
            '''
            修改商品信息,可进行部分字段更新
            :param shopId:
            :return:
            '''
            if not current_user.has_role('shop_seller') and current_user.id != shopId:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="没有权限")
            args = reqparse.RequestParser() \
                .add_argument('id', type=int, location='json', required=True, help='商品id不能为空') \
                .add_argument('name', type=str, location='json') \
                .add_argument('logo', type=str, location='json') \
                .add_argument('category', type=str, location='json') \
                .add_argument('price', type=float, location='json') \
                .add_argument('description', type=str, location='json') \
                .add_argument('remain', type=int, location='json') \
                .parse_args()
            args['seller_id'] = current_user.id
            args = dict(filter(lambda item: item[1] is not None, args.items()))
            if Shop_Itemlist(id=args['id']).update(**args):
                return Response(message="修改成功")
            else:
                return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='修改失败')

        @auth_token_required
        def delete(self, shopId):
            '''
            删除商品
            :param shopId:
            :return:
            '''
            if not current_user.has_role('shop_seller') and current_user.id != shopId:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="没有权限")
            args = reqparse.RequestParser() \
                .add_argument('id', type=int, location='args') \
                .add_argument('category', type=str, location='args') \
                .parse_args()
            if args.get('id', None):
                Shop_Itemlist(seller_id=current_user.id).delete(id=args['id'])  # 根据id删除Item
            elif args.get('category', None):
                Shop_Itemlist(seller_id=current_user.id).delete(category=args['category'])  # 根据类别删除Item
            else:
                return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='缺少id或category参数')
            return Response(message='删除成功')

    class Order(Resource):
        @auth_token_required
        def get(self, shopId):
            args = reqparse.RequestParser() \
                .add_argument('start_time', type=str, location='args', default=datetime.date(datetime.now())) \
                .add_argument('end_time', type=str, location='args',
                              default=datetime.date(datetime.now() + timedelta(days=1))) \
                .parse_args()
            if current_user.id == shopId and current_user.has_role('shop_seller'):
                order = Shop_Seller(id=shopId).orderList(start_time=args['start_time'], end_time=args['end_time'])
                order = marshal(order, output_order)
                return Response(message='获取成功', data=order)
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

        @auth_token_required
        def post(self, shopId):
            '''
            创建订单
            :param shopId:
            :return:
            '''
            if current_user.id == shopId:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='不能向自己下单')
            args = reqparse.RequestParser() \
                .add_argument('building', type=str, location='json', required=True, help='楼栋名称不能为空') \
                .add_argument('address', type=str, location='json', required=True, help='收货地址不能为空') \
                .add_argument('remark', type=str, location='json') \
                .add_argument('detail', type=dict, action='append', required=True, help='订单内容不能为空') \
                .parse_args()
            result = Shop_Orderlist(seller_id=shopId, user_id=current_user.id).add(**args)
            if result is True:
                try:
                    jpush_msg('咕噜外卖', '新订单提醒', User(id=shopId).get().push_id)
                except:
                    pass
                finally:
                    return Response(code=HttpStatus.HTTP_201_CREATED, message='下单成功')
            else:
                return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message=result)

        @auth_token_required
        def put(self, shopId):
            '''
            改变订单状态
            :param shopId:
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('order_id', type=str, location='json', required=True, help='订单id不能为空') \
                .add_argument('status', type=int, location='json', required=True, help='订单状态不能为空') \
                .add_argument('remark', type=str, location='json') \
                .parse_args()
            if current_user.has_role('shop_seller') and shopId == current_user.id:
                if Shop_Orderlist(order_id=args['order_id'], seller_id=current_user.id).update(status=args['status'],
                                                                                               remark=args['remark']):
                    return Response(message='修改成功')
            elif Shop_Orderlist(order_id=args['order_id'], user_id=current_user.id).update(status=args['status'],
                                                                                           remark=args['remark']):
                if args['status'] == Shop_Orderlist.OrderStatus.CANCELLING:
                    try:
                        jpush_msg('咕噜外卖', '退单提醒', User(id=shopId).get().push_id)
                    except:
                        pass
                return Response(message='修改成功')
            return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message='修改失败')

    class Status(Resource):
        @auth_token_required
        def put(self, shopId):
            '''
            改变商家状态
            :param shopId:
            :return:
            '''
            args = reqparse.RequestParser() \
                .add_argument('status', type=int, location='json', required=True, help='商家状态不能为空') \
                .parse_args()
            if (current_user.has_role('shop_seller') and current_user.id == shopId) \
                    or (current_user.has_role('shop_admin') or current_user.has_role('admin')):
                Shop_Seller(id=shopId).status = args['status']
                return Response(message='修改成功')
            return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='无权修改状态')
