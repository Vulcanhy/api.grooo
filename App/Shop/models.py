__author__ = 'Vulcanhy & responsible'
import random
from .decorator import *
from .. import db
from ..Account.models import User, School, School_Building
from .. import cache


class Shop_Config(db.Model):
    class ShopStatus:
        CLOSED = 0
        OPENING = 1

    school_id = db.Column(db.Integer, db.ForeignKey(School.id), primary_key=True)
    _announcement = db.Column('announcement', db.Text)
    _status = db.Column('status', db.SmallInteger, default=ShopStatus.OPENING)
    _status_remark = db.Column('status_remark', db.String(50))

    @property
    def announcement(self):
        @cache.cached(timeout=120, key_prefix='{}-{}-{}'.format(self.__class__, 'announcement', self.school_id))
        def cached():
            config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
            return config._announcement

        return cached()

    @announcement.setter
    def announcement(self, announcement):
        config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
        config._announcement = announcement
        db.session.commit()

    @property
    def status(self):
        @cache.cached(timeout=120, key_prefix='{}-{}-{}'.format(self.__class__, 'status', self.school_id))
        def cached():
            config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
            return config._status

        return cached()

    @status.setter
    def status(self, status):
        if status in [Shop_Config.ShopStatus.OPENING, Shop_Config.ShopStatus.CLOSED]:
            config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
            config._status = status
            db.session.commit()

    @property
    def status_remark(self):
        @cache.cached(timeout=120, key_prefix='{}-{}-{}'.format(self.__class__, 'status_remark', self.school_id))
        def cached():
            config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
            return config._status_remark

        return cached()

    @status_remark.setter
    def status_remark(self, status_remark):
        config = Shop_Config.query.filter(Shop_Config.school_id == self.school_id).first()
        config._status_remark = status_remark
        db.session.commit()


class Shop_User(db.Model):
    id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    building = db.Column(db.String(20), db.ForeignKey(School_Building.name))
    address = db.Column(db.String(50))
    basic_user = db.relationship(User, uselist=True, lazy='dynamic')

    @property
    def profile(self):
        user = Shop_User.query.get(self.id)
        return user

    @profile.setter
    def profile(self, prof):
        user = Shop_User.query.get(self.id)
        if user:
            user.building = prof.get('building', user.building)
            user.address = prof.get('address', user.address)
        else:
            user = Shop_User(id=self.id, **prof)
            db.session.add(user)
        db.session.commit()

    @property
    def orderList(self):
        order = Shop_Orderlist.query.filter(Shop_Orderlist.user_id == self.id).order_by(
            Shop_Orderlist.time.desc()).limit(50).all()
        return order


class Shop_Seller(db.Model):
    class SellerStatus:
        CLOSED = 0
        OPENED = 1

    id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey(School.id))
    category = db.Column(db.String(20), default='外卖', nullable=False)  # 可自定义商家类别，如外卖，超市
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    logo = db.Column(db.String(255), default='')
    description = db.Column(db.String(50), default='')
    basePrice = db.Column(db.Float, default=0)  # 最低消费
    activity = db.Column(db.Text, default='')  # 以&&分割
    rating = db.Column(db.Float, default=0)
    rateNumber = db.Column(db.Integer, default=0)
    monthSold = db.Column(db.Integer, default=0)
    _start_time = db.Column('start_time', db.Text, default='')  # 自动营业时间点
    _stop_time = db.Column('stop_time', db.Text, default='')  # 自动停业时间点
    weight = db.Column(db.SmallInteger, default=5)  # 权重,商家排序相关
    _status = db.Column('status', db.SmallInteger, default=SellerStatus.CLOSED)
    active = db.Column(db.Boolean, default=True)
    itemList = db.relationship('Shop_Itemlist', lazy='dynamic')
    _orderList = db.relationship('Shop_Orderlist', backref=db.backref('Shop_Seller'), lazy='dynamic')

    @classmethod
    def add(cls, **info):
        seller = Shop_Seller(**info)
        db.session.add(seller)
        db.session.commit()
        return seller

    def update(self, **info):
        seller = Shop_Seller.query.get(self.id)
        seller.category = info.get('category', seller.category)
        seller.name = info.get('name', self.name)
        seller.phone = info.get('phone', seller.phone)
        seller.logo = info.get('logo', seller.logo)
        seller.description = info.get('description', seller.description)
        seller.basePrice = info.get('basePrice', seller.basePrice)
        seller.activity = info.get('activity', seller.activity)
        seller.start_time = info.get('start_time', seller.start_time)
        seller.stop_time = info.get('stop_time', seller.stop_time)
        seller.weight = info.get('weight', seller.weight)
        seller.status = info.get('status', seller.status)
        seller.active = info.get('active', seller.active)
        db.session.commit()
        return True

    def orderList(self, start_time, end_time):
        order = Shop_Seller.query.get(self.id)._orderList.filter(
            Shop_Orderlist.time.between(start_time, end_time)).order_by(-Shop_Orderlist.time).all()
        return order

    @property
    def ratingList(self):
        order = Shop_Seller.query.get(self.id)._orderList.filter(
            Shop_Orderlist.status == Shop_Orderlist.OrderStatus.RATED).order_by(-Shop_Orderlist.time).limit(50).all()
        return order

    def get(self, rand=False, includeDisabledSeller=False):
        if self.id:
            return Shop_Seller.query.filter(Shop_Seller.id == self.id).first()
        seller = Shop_Seller.query.filter(Shop_Seller.school_id == self.school_id,
                                          Shop_Seller.active == True if not includeDisabledSeller else True) \
            .order_by(-Shop_Seller.weight).all()
        return [random.choice(seller)] if rand else seller

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status=None):
        seller = Shop_Seller.query.get(self.id)
        seller._status = status
        db.session.commit()

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, time_list):
        self._start_time = str(time_list)

    @property
    def stop_time(self):
        return self._stop_time

    @stop_time.setter
    def stop_time(self, time_list):
        self._stop_time = str(time_list)


class Shop_Itemlist(db.Model):
    __table_args__ = (
        db.UniqueConstraint('seller_id', 'name', 'category', 'price', name='uix_1'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_id = db.Column(db.Integer, db.ForeignKey(Shop_Seller.id), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    logo = db.Column(db.String(255), default='')
    category = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(20), default='')
    remain = db.Column(db.Integer, default=99999)
    monthSold = db.Column(db.Integer, default=0)

    @classmethod
    def add(cls, **Item):
        item = Shop_Itemlist(**Item)
        db.session.add(item)
        db.session.commit()
        return True

    def update(self, **Item):
        item = Shop_Itemlist.query.filter(Shop_Itemlist.id == self.id,
                                          Shop_Itemlist.seller_id == Item.get('seller_id')).first()
        if item:
            item.name = Item.get('name', item.name)
            item.logo = Item.get('logo', item.logo)
            item.category = Item.get('category', item.category)
            item.price = Item.get('price', item.price)
            item.description = Item.get('description', item.description)
            db.session.commit()
            return True
        else:
            return False

    def delete(self, id=None, category=None):
        item = Shop_Itemlist.query
        if id:
            item = item.filter(Shop_Itemlist.seller_id == self.seller_id, Shop_Itemlist.id == id)
        elif category:
            item = item.filter(Shop_Itemlist.seller_id == self.seller_id, Shop_Itemlist.category == category)
        if item.count() > 0:
            item.delete()
            db.session.commit()
            return True
        else:
            return False


class Shop_Orderlist(db.Model):
    class OrderStatus:
        ORDERED = 00  # 未处理
        ACCEPTED = 10  # 已接单
        CANCELLING = 20  # 用户申请退单
        USER_CANCELLED = 21  # 用户退单完成
        SELLER_CANCELLED = 22  # 商家直接取消订单
        FINISHED = 30  # 已完成
        RATED = 31  # 已评价

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_id = db.Column(db.Integer, db.ForeignKey(Shop_Seller.id))
    seller = db.relationship('Shop_Seller')
    user = db.relationship('User', backref='Shop_Orderlist')
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    order_id = db.Column(db.String(20), nullable=False, unique=True)  # 格式：年+月+日+四位学校id+六位订单id
    price = db.Column(db.Float, nullable=False)
    detail = db.relationship('Shop_OrderDetail', backref='Shop_Orderlist')
    building = db.Column(db.String(20), db.ForeignKey(School_Building.name), nullable=False)  # 楼栋名称
    address = db.Column(db.String(50), nullable=False)  # 具体地址
    remark = db.Column(db.String(50), default='')
    status = db.Column(db.Integer, default=OrderStatus.ORDERED)
    status_remark = db.Column(db.String(20), default='')  # 订单状态附加信息
    rating = db.Column(db.Integer, default=0)
    rating_remark = db.Column(db.String(100), default='')
    time = db.Column(db.DateTime, nullable=False)

    @checkSchoolStatus
    @checkSellerStatus
    @checkOrderFrequency(interval=60)
    @checkOrderValidity
    def add(self, detail, building, address, remark):
        totalPrice = 0
        seller = Shop_Seller.query.get(self.seller_id)
        self.order_id = '{0.year:4}{0.month:02}{0.day:02}{1:04}{2:2}{3:4}{4:2}' \
            .format(datetime.now(),
                    seller.school_id,
                    random.randint(10, 99),
                    '{0:04}'.format(Shop_Orderlist.query.count() + 1)[-4:],
                    random.randint(10, 99))
        order = Shop_Orderlist(seller_id=self.seller_id, user_id=self.user_id, order_id=self.order_id, price=0,
                               building=building, address=address, remark=remark, time=datetime.now())
        db.session.add(order)  # 为了保证添加Shop_OrderDetail时order_id的依赖关系
        for item in detail:
            # detail格式:[{"id":id,"count":count},]
            Item = Shop_Itemlist.query.filter(Shop_Itemlist.id == item['id'],
                                              Shop_Itemlist.seller_id == self.seller_id).first()
            totalPrice += Item.price * item['count']
            Item = Shop_OrderDetail(name=Item.name, count=item['count'], price=Item.price, order_id=self.order_id)
            db.session.add(Item)
        if totalPrice <= 0:
            return "订单内容无效(总额为0)"
        if totalPrice < seller.basePrice:
            return "不满足最低消费"
        Shop_Orderlist.query.filter(Shop_Orderlist.order_id == self.order_id).first().price = totalPrice
        db.session.commit()
        return True

    def update(self, status, remark=None):
        order = Shop_Orderlist.query.filter(Shop_Orderlist.order_id == self.order_id)
        if self.seller_id is not None:
            order = order.filter(Shop_Orderlist.seller_id == self.seller_id).first()
        elif self.user_id is not None:
            order = order.filter(Shop_Orderlist.user_id == self.user_id).first()
        if order.status > status:  # 检查status是否符合逻辑
            return False
        # 检查用户身份请求status是否符合逻辑
        if self.user_id is not None and status not in [Shop_Orderlist.OrderStatus.CANCELLING,
                                                       Shop_Orderlist.OrderStatus.FINISHED]:
            return False
        # 检查商家身份请求status是否符合逻辑
        if self.seller_id is not None and status not in [Shop_Orderlist.OrderStatus.ACCEPTED,
                                                         Shop_Orderlist.OrderStatus.USER_CANCELLED,
                                                         Shop_Orderlist.OrderStatus.SELLER_CANCELLED]:
            return False
        order.status = status
        if status in [Shop_Orderlist.OrderStatus.CANCELLING, Shop_Orderlist.OrderStatus.SELLER_CANCELLED]:
            order.remark = remark
        db.session.commit()
        return True

    def rate(self, rating, rate_remark):
        order = Shop_Orderlist.query.filter(Shop_Orderlist.user_id == self.user_id,
                                            Shop_Orderlist.order_id == self.order_id).first()
        if order.status == Shop_Orderlist.OrderStatus.FINISHED and (1 <= rating <= 5):
            order.rating = rating
            order.rating_remark = rate_remark
            order.status = Shop_Orderlist.OrderStatus.RATED
            order.user.score += order.price / 10  # 每10元获得1积分
            order.seller.rating = (order.seller.rating * order.seller.rateNumber + rating) / (
                order.seller.rateNumber + 1)
            order.seller.rateNumber += 1
            db.session.commit()
            return True
        else:
            return False


class Shop_OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(20), db.ForeignKey(Shop_Orderlist.order_id))
    name = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=False)  # 单价
    count = db.Column(db.Integer, nullable=False)
