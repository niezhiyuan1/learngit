#coding:utf-8
from trytond.pyson import Eval
from trytond.model import fields
from trytond.pool import PoolMeta, Pool

__all__ = ['Purchase']


class Purchase:
    __metaclass__  = PoolMeta
    __name__ = "purchase.purchase"

    delivery_place = fields.Many2One('stock.location', 'delivery_place', readonly=True, select=True, required=True)
    internal_order = fields.Integer('internal_order', select=True, readonly=True)
    party_ = fields.Many2One('party.party', 'Party',
                             states={
                                 'readonly': ((Eval('state') != 'draft')
                                              | (Eval('lines', [0]) & Eval('party'))),
                             },
                             select=True, domain=[('type_', '=', 'supplier')], depends=['state'])

    @fields.depends('party', 'party_')
    def on_change_party_(self):
        if self.party_:
            Purchase = Pool().get('purchase.purchase')
            self.party = self.party_.id
            Purchase.on_change_party(self)

    @staticmethod
    def default_delivery_place():
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        return warehouse

    @staticmethod
    def default_internal_order():
        return 0

    @staticmethod
    def default_warehouse():
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        return warehouse