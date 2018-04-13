__author__ = 'Vulcanhy & responsible'
import re
from flask.ext.restful import Resource, reqparse, fields, marshal
from flask.ext.security import auth_token_required, current_user, login_user
from qiniu import Auth
from .. import db
from .. import config
from .models import User, School, roles_users, Role
from ..common.response import Response, HttpStatus

output_userToken = {
    "id": fields.Integer,
    "token": fields.String(attribute=lambda user: user.get_auth_token()),
    "roles": fields.Nested({
        "id": fields.Integer
    })
}

output_userProfile = {
    "id": fields.Integer,
    "email": fields.String,
    "nickname": fields.String,
    "avatar": fields.String,
    "score": fields.Float,
    "school": fields.Nested({
        "id": fields.Integer,
        "name": fields.String
    })
}

output_userRole = {
    "username": fields.String,
    "roles": fields.Nested({
        "id": fields.Integer(attribute='id'),
        "description": fields.String(attribute='description')
    })
}

output_school = {
    "id": fields.Integer,
    "name": fields.String
}


class Account(Resource):
    def post(self):
        '''
        创建新用户
        :param username:用户名
        :param password:密码
        :return:Response
        '''
        args = reqparse.RequestParser() \
            .add_argument("username", type=str, location='json', required=True, help="用户名不能为空") \
            .add_argument("password", type=str, location='json', required=True, help="密码不能为空") \
            .add_argument("school_id", type=int, location='json', required=True, help="学校不能为空") \
            .parse_args()  # 读取参数
        if User(username=args['username']).get() is not None:
            return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message="此用户已存在")
        if re.match(re.compile('1[0-9]{10}'), args['username']) is None:
            return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message="不是有效的手机号")
        User.add(args['username'], args['password'], args['school_id'])
        return Response(code=HttpStatus.HTTP_201_CREATED, message="创建成功")

    @auth_token_required
    def put(self):
        '''
        修改密码
        :return:
        '''
        args = reqparse.RequestParser() \
            .add_argument("username", type=str, location='json') \
            .add_argument("newPassword", type=str, location='json', required=True, help="新密码不能为空") \
            .parse_args()
        username = current_user.username
        if args.get('username') not in ['', None]:
            if current_user.has_role('superadmin') or (
                        current_user.has_role('admin') and current_user.school_id == User(
                        username=args['username']).get().school_id):
                username = args['username']
            else:
                return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message="没有权限")
        if User(username=username).changePassword(args['newPassword']):
            return Response(code=HttpStatus.HTTP_200_OK, message="修改成功")
        return Response(code=HttpStatus.HTTP_400_BAD_REQUEST, message="修改失败")


class Schools(Resource):
    def get(self):
        school = School().get()
        school = marshal(school, output_school)
        return Response(data=school)


class Token(Resource):
    def post(self):
        '''
        用户登录获取Token
        :return: Token
        '''
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='json', required=True, help="用户名不能为空") \
            .add_argument("password", type=str, location='json', required=True, help="密码不能为空") \
            .parse_args()
        user = User.authenticate(args['username'], args['password'])
        if isinstance(user, User):
            login_user(user=user)
            return Response(message='登录成功', data=marshal(user, output_userToken))
        else:
            return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message=user)


class Profile(Resource):
    def get(self, userId):
        user = User(id=userId).get()
        if user:
            return Response(data=marshal(user, output_userProfile))
        else:
            return Response(code=HttpStatus.HTTP_404_NOT_FOUND, message='无此用户')

    @auth_token_required
    def put(self, userId):
        if userId != current_user.id:
            return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='无权修改')
        args = reqparse.RequestParser() \
            .add_argument('email', type=str, location='json') \
            .add_argument('nickname', type=str, location='json') \
            .add_argument('avatar', type=str, location='json') \
            .add_argument('push_id', type=str, location='json') \
            .parse_args()
        args = dict(filter(lambda item: item[1] is not None, args.items()))
        if User(id=current_user.id).update(args):
            return Response(message='修改成功')


class Roles(Resource):
    allow_mapping = {
        1: [1, 2, 3, 4, 5],
        2: [2, 3, 4, 5],
        3: [4],
        4: [],
        5: []
    }

    @auth_token_required
    def get(self):
        if current_user.has_role('superadmin'):
            roleList = User.query.all()
            roleList = list(filter(lambda user: len(user.roles) > 0, roleList))
            roleList = marshal(roleList, output_userRole)
            return Response(code=HttpStatus.HTTP_200_OK, data=roleList)
        elif current_user.has_role('admin'):
            roleList = User.query.filter(User.school_id == current_user.school_id).all()
            roleList = list(filter(lambda user: len(user.roles) > 0, roleList))
            roleList = marshal(roleList, output_userRole)
            return Response(code=HttpStatus.HTTP_200_OK, data=roleList)
        return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    @auth_token_required
    def post(self):
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='json', required=True, help="用户名不能为空") \
            .add_argument('role_id', type=int, location='json', required=True, help="role_id不能为空") \
            .parse_args()
        if args['role_id'] in self.allow_mapping[min([role.id for role in current_user.roles])]:
            if current_user.has_role('superadmin'):
                user = User(username=args['username']).get()
                user.roles.append(Role.query.get(args['role_id']))
                db.session.commit()
                return Response(code=HttpStatus.HTTP_200_OK)
            elif current_user.has_role('admin'):
                user = User(username=args['username']).get()
                if user.school_id == current_user.school_id:
                    user.roles.append(Role.query.get(args['role_id']))
                    db.session.commit()
                    return Response(code=HttpStatus.HTTP_200_OK)
        return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    @auth_token_required
    def delete(self):
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='json', required=True, help="用户名不能为空") \
            .add_argument('role_id', type=int, location='json', required=True, help="role_id不能为空") \
            .parse_args()
        if args['role_id'] in self.allow_mapping[min([role.id for role in current_user.roles])]:
            if current_user.has_role('superadmin'):
                user = User(username=args['username']).get()
                user.roles.remove(Role.query.get(args['role_id']))
                db.session.commit()
                return Response(code=HttpStatus.HTTP_200_OK)
            elif current_user.has_role('admin'):
                user = User(username=args['username']).get()
                if user.school_id == current_user.school_id:
                    user.roles.remove(Role.query.get(args['role_id']))
                    db.session.commit()
                    return Response(code=HttpStatus.HTTP_200_OK)
        return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')


class Status(Resource):
    @auth_token_required
    def post(self):
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='json', required=True, help="用户名不能为空") \
            .parse_args()
        user = User(username=args['username']).get()
        if current_user.has_role('superadmin') or (
                        current_user.school_id == user.school_id and current_user.has_role('admin')):
            User(username=args['username']).enable()
            return Response(code=HttpStatus.HTTP_200_OK, message="启用成功")
        else:
            return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')

    @auth_token_required
    def delete(self):
        '''
        禁用账户
        :return:
        '''
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='json', required=True, help="用户名不能为空") \
            .parse_args()
        user = User(username=args['username']).get()
        if current_user.has_role('superadmin') or (
                        current_user.school_id == user.school_id and current_user.has_role('admin')):
            User(username=args['username']).disable()
            return Response(code=HttpStatus.HTTP_200_OK, message="禁用成功")
        else:
            return Response(code=HttpStatus.HTTP_403_FORBIDDEN, message='没有权限')


class FileToken(Resource):
    @auth_token_required
    def get(self):
        args = reqparse.RequestParser() \
            .add_argument('username', type=str, location='args', required=False) \
            .add_argument('uid', type=int, location='args', required=False) \
            .parse_args()
        token = ''
        user = None
        if args.get("username", None) is not None:
            user = User(username=args["username"])
        elif args.get("uid", None) is not None:
            user = User(id=args["uid"])
        else:
            user = current_user
        if args.get("username", None) is not None and \
                (current_user.has_role('superadmin') or (
                                current_user.school_id == user.school_id and
                            current_user.has_role('admin'))):
            token = Auth(config.QINIU_ACCESS_KEY, config.QINIU_SECRET_KEY) \
                .upload_token(bucket='grooo', key=user.id, expires=60 * 3, policy={
                "insertOnly": 0,
                "fsizeLimit": 1024 * 1024,
                "mimeLimit": "image/*"
            })
        token = Auth(config.QINIU_ACCESS_KEY, config.QINIU_SECRET_KEY) \
            .upload_token(bucket='grooo', key=user.id, expires=60 * 3, policy={
            "insertOnly": 0,
            "fsizeLimit": 1024 * 1024,
            "mimeLimit": "image/*"
        })
        return Response(data={'uptoken': token})
