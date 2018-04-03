#coding:utf-8
from trytond.model import fields
from trytond.pool import PoolMeta, Pool

__all__ = ['PurchaseLine']

class PurchaseLine:
    __metaclass__  = PoolMeta
    __name__ = "purchase.line"

