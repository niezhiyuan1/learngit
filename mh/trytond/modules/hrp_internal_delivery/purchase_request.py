#coding:utf-8
from trytond.model import  fields
from trytond.pool import  PoolMeta

__all__ = ['PurchaseRequest']

class PurchaseRequest:
    __metaclass__  = PoolMeta
    __name__ = "purchase.request"

    is_direct_sending = fields.Boolean('is_direct_sending',select=True)

