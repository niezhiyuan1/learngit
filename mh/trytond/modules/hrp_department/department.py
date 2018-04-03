# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime

from trytond.model import fields, Unique
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from trytond.model import ModelView, ModelSQL, fields
from trytond.config import config

__all__ = ['Department']

VAT_COUNTRIES = [('', '')]
STATES = {
    'readonly': ~Eval('active', True),
}
DEPENDS = ['active']

price_digits = (16, config.getint('product', 'price_decimal', default=4))


class Department(ModelSQL, ModelView):
    """Department"""
    __name__ = "hrp_department.department"

    mark = fields.Many2One('party.party', 'Mark', select=True)
    department_name = fields.Function(fields.Char('Name', select=True), 'get_name', 'set_name')
    department_code = fields.Function(fields.Char('Code', select=True), 'get_code', 'set_code')
    deivery = fields.Function(fields.Boolean('Delivery'), 'get_deivery', 'set_deivery')
    invoice = fields.Function(fields.Boolean('Invoice', readonly=False), 'get_invoice', 'set_invoice')
    active = fields.Function(
        fields.Boolean('Active', select=True, readonly=True), "get_active", "set_active", 'seacher_active')
    address_active = fields.Function(
        fields.Boolean('Address_active'), 'get_address_active', 'set_address_active', 'seacher_active_address')

    @classmethod
    def __setup__(cls):
        super(Department, cls).__setup__()
        # t = cls.__table__()
        # cls._sql_constraints = [
        #     ('department_code_uniq', Unique(t, t.department_code),
        #      u'科室编码必须唯一.')
        # ]

    def get_name(self, name):
        """

        :param  name:
        :return:
        """
        return self.mark.name

    def get_code(self, name):
        kkl = self.mark
        return self.mark.addresses[0].name

    def get_deivery(self, name):
        return self.mark.addresses[0].deivery

    def get_active(self, name):
        return self.mark.active

    def get_address_active(self, name):
        return self.mark.addresses[0].active

    def get_invoice(self, name):
        return self.mark.addresses[0].invoice

    @classmethod
    def set_address_active(cls, set_address_active, name, value):
        pass

    @classmethod
    def set_deivery(cls, set_deivery, name, value):
        pass

    @classmethod
    def set_code(cls, set_code, name, value):
        pass

    @classmethod
    def set_name(cls, set_name, name, value):
        pass

    @classmethod
    def set_active(cls, set_active, name, value):
        pass

    @classmethod
    def set_invoice(cls, set_invoice, name, value):
        pass

    @classmethod
    def seacher_active(cls, name, clause):
        pass

    @classmethod
    def seacher_active_address(cls, name, clause):
        pass

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_address_active():
        return True

    @staticmethod
    def default_invoice():
        return False

    @staticmethod
    def default_deivery():
        return True

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        party_partys = pool.get("party.party")
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        party_configuration = pool.get("product.configuration")
        party_configurations = party_configuration.search([])[0]
        party_addresss = pool.get("party.address")
        for value in vlist:
            name = value['department_name']
            code = value['department_code']
            active = True
            try:
                account_payable = party_configurations.account_payable.id
            except AttributeError:
                cls.raise_user_error(u'请先填写采购配置！')
            try:
                supplier_payment_term = config.supplier_payment_term.id
            except AttributeError:
                cls.raise_user_error(u'请先填写采购配置！')
            add_each = [{'name': name,
                         'active': active,
                         'account_payable': party_configurations.account_payable.id,
                         'account_receivable': party_configurations.account_receivable.id,
                         'type_': 'client',
                         'supplier_payment_term': supplier_payment_term,
                         'customer_payment_term': supplier_payment_term
                         }]

            party_party = party_partys.create(add_each)
            marks = int(party_party[0].id)
            party_addresss.create([{'party': marks,
                                    'name': code,
                                    'invoice': False,
                                    'delivery': True,
                                    'active': True}])
            value['mark'] = marks
        return super(Department, cls).create(vlist)

    @classmethod
    def delete(cls, records):
        pool = Pool()
        party_partys = pool.get("party.party")
        party_addresss = pool.get("party.address")
        for value in records:
            mark = int(value.mark)

            party_party = party_partys.search([
                ('id', '=', mark)
            ])
            party_address = party_addresss.search([
                ('party', '=', mark)
            ])
            party_addresss.delete(party_address)
            party_partys.delete(party_party)
        return super(Department, cls).delete(records)

    @classmethod
    def write(cls, records, values, *args):
        pool = Pool()
        party_partys = pool.get("party.party")
        party_addresss = pool.get("party.address")
        for ids in records:
            mark = int(ids.mark)
            party_party = party_partys.search([
                ('id', '=', mark)
            ])
            party_address = party_addresss.search([
                ('party', '=', mark)
            ])
            lv = {}
            lvc = {}
            if 'department_code' in values:
                lv['name'] = values['department_code']
            if lv != {}:
                party_addresss.write(party_address, lv)
            if 'department_name' in values:
                lvc['name'] = values['department_name']
            if 'active' in values:
                lvc['active'] = values['active']
            if lvc != {}:
                party_partys.write(party_party, lvc)
        return super(Department, cls).write(records, values)
