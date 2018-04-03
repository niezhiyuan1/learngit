# -*- coding: UTF-8 -*-
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta

from trytond.model import ModelView, ModelSQL, fields


__all__ = ['Location']
class Location:
    "Location"
    __metaclass__ = PoolMeta
    __name__ = 'stock.location'
    is_freeze = fields.Boolean('is_freeze')
    is_goods = fields.Boolean('is_goods')
    ceiling = fields.Float('ceiling')
    freeze_location = fields.Many2One(
        "stock.location", "Freeze", states={
            'invisible': Eval('type') != 'warehouse',
            'readonly': ~Eval('active'),
            'required': Eval('type') == 'warehouse',
        },
        domain=[
            ('type', 'in', ['storage', 'view']),
            ['OR',
                ('parent', 'child_of', [Eval('id')]),
                ('parent', '=', None)]],
        depends=['type', 'active', 'id'])

    @staticmethod
    def default_is_goods():
        return False

    @classmethod
    def create(cls, vlist):
        for value in vlist:
            if not value['code']:
                pass
            elif value['code'] and value['code'].isalpha() and len(value['code']) == 1:
                pass
            else:
                cls.raise_user_error(u'请按规则填写编码!')
        return super(Location, cls).create(vlist)
