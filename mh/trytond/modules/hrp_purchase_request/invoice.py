# coding:utf-8
from trytond.model import fields
from trytond.pool import PoolMeta, Pool

__all__ = ['Invoice']


class Invoice:
    __metaclass__ = PoolMeta
    __name__ = "account.invoice"

    amount = fields.Numeric('amount', select=True, digits=(16, 4))
