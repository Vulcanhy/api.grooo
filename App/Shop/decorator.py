__author__ = 'Vulcanhy & responsible'
from functools import wraps
from datetime import datetime, timedelta


def checkSellerStatus(func):
    from .models import Shop_Seller
    @wraps(func)
    def wrapper(*args, **kwargs):
        seller = Shop_Seller.query.get(args[0].seller_id)
        if seller.status == Shop_Seller.SellerStatus.CLOSED:
            return '商家已休息'
        if seller.active == False:
            return '商家已无效'
        return func(*args, **kwargs)

    return wrapper


def checkOrderValidity(func):
    from .models import Shop_Itemlist
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(kwargs['detail']) == 0:
            return '订单内容不能为空'
        for item in kwargs['detail']:
            Item = Shop_Itemlist.query.filter(Shop_Itemlist.id == item['id'],
                                              Shop_Itemlist.seller_id == args[0].seller_id).first()
            if Item is None:
                return '订单内容不合法'
        return func(*args, **kwargs)

    return wrapper


def checkOrderFrequency(interval=60):
    from .models import Shop_User
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lastOrder = Shop_User(id=args[0].user_id).orderList
            if lastOrder and (datetime.now() - lastOrder[0].time < timedelta(seconds=interval)):
                return '距您上次下单还不到{}秒喔，休息一会儿再下单吧'.format(interval)
            return func(*args, **kwargs)

        return wrapper

    return decorate


def checkSchoolStatus(func):
    from .models import Shop_Config, Shop_Seller
    @wraps(func)
    def wrapper(*args, **kwargs):
        school = Shop_Config(school_id=Shop_Seller(id=args[0].seller_id).get().school_id)
        if school.status == Shop_Config.ShopStatus.CLOSED:
            return school.status_remark
        return func(*args, **kwargs)

    return wrapper
