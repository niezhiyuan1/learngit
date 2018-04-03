# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime

from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from trytond.model import ModelView, ModelSQL, fields
from trytond.config import config

__all__ = ['New_party', 'Party']

VAT_COUNTRIES = [('', '')]
STATES = {
    'readonly': ~Eval('active', True),
}
DEPENDS = ['active']

price_digits = (16, config.getint('product', 'price_decimal', default=4))


class Party:
    "Party"
    __metaclass__ = PoolMeta
    __name__ = 'party.party'
    new_name = fields.Char('Name1', select=True)
    finance_code = fields.Char('finance_code', select=True)
    settlement = fields.Char('settlement', select=True)
    currency = fields.Char('currency', select=True)
    phone = fields.Char('phone', select=True)
    contact_name = fields.Char('contact_name', select=True)
    type_ = fields.Selection([
        ('supplier', u'供应商'),
        ('client', u'客户'),
    ], 'Type', select=True)


class New_party(ModelSQL, ModelView):
    "New_party"
    __name__ = "hrp_party.new_party"

    new_name = fields.Char('Name1', select=True)
    finance_code = fields.Char('finance_code', select=True)
    settlement = fields.Char('settlement', select=True)
    currency = fields.Char('currency', select=True)
    phone = fields.Char('phone', select=True)
    contact_name = fields.Char('contact_name', select=True)
    #############################
    mark = fields.Many2One('party.party', 'Mark', select=True)
    code = fields.Function(fields.Char('Code', select=True, states=STATES, required=True, depends=DEPENDS), 'get_codes',
                           'set_code')
    name = fields.Function(fields.Char('Name', select=True, required=True, states=STATES, depends=DEPENDS), 'get_names',
                           'set_name')
    supplier_payment_term = fields.Function(fields.Property(fields.Many2One(
        'account.invoice.payment_term', string='Supplier Payment Term', required=True)), 'get_supplier_payment_term',
        'set_supplier_payment_term')
    street = fields.Function(fields.Char('Street', states=STATES, depends=DEPENDS), 'get_street', 'set_street')
    invoice = fields.Function(fields.Boolean('Invoice', readonly=False), 'get_invoice', 'set_invoice')
    deivery = fields.Function(fields.Boolean('Delivery', readonly=False), 'get_deivery', 'set_deivery')
    active = fields.Function(fields.Boolean('Active', select=True), "get_active", "set_active", 'seacher_active')
    address_active = fields.Function(fields.Boolean('Address_active', readonly=False), 'get_address_active',
                                     'set_address_active', 'seacher_active_address')

    @classmethod
    def __setup__(cls):
        super(New_party, cls).__setup__()

    def get_names(self, name):
        Party = Pool().get('party.party')
        # return self.mark.name
        sdsd = self.id
        sdssd = self.mark
        return self.mark.name

    def get_codes(self, name):
        Party = Pool().get('party.party')
        New_party = Pool().get('hrp_party.new_party')
        sdsd = New_party(self.id)

        sddsaaa = New_party.search([('id', '=', self.id)])
        sdc = sddsaaa[0].create_date
        sdssd = sddsaaa[0].mark
        return self.mark.code

    def get_supplier_payment_term(self, name):
        return self.mark.supplier_payment_term.id

    def get_street(self, name):
        return self.mark.addresses[0].street

    def get_invoice(self, name):
        return self.mark.addresses[0].invoice

    def get_deivery(self, name):
        return self.mark.addresses[0].delivery

    def get_active(self, name):
        return self.mark.active

    def get_address_active(self, name):
        return self.mark.addresses[0].active

    @classmethod
    def set_supplier_payment_term(cls, set_supplier_payment_term, name, value):
        pass

    @classmethod
    def set_street(cls, set_street, name, value):
        pass

    @classmethod
    def set_code(cls, set_code, name, value):
        pass

    @classmethod
    def set_active(cls, set_active, name, value):
        pass

    @classmethod
    def set_invoice(cls, set_invoice, name, value):
        pass

    @classmethod
    def set_name(cls, set_name, name, value):
        pass

    @classmethod
    def set_address_active(cls, set_address_active, name, value):
        pass

    @classmethod
    def set_deivery(cls, set_deivery, name, value):
        pass

    @classmethod
    def seacher_active(cls, name, clause):
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
        return True

    @staticmethod
    def default_deivery():
        return True

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        party_partys = pool.get("party.party")
        party_configuration = pool.get("product.configuration")
        party_configurations = party_configuration.search([])[0]
        party_addresss = pool.get("party.address")
        for value in vlist:
            party_ = party_partys.search([('name', '=', value['name'])])
            if party_:
                continue
            name = value['name']
            code = value['code']
            active = value['active']
            supplier_payment_term = value['supplier_payment_term']
            street = value['street']
            invoice = value['invoice']
            delivery = value['deivery']
            address_active = value['address_active']
            add_each = [{'name': name,
                         'active': active,
                         'account_payable': party_configurations.account_payable.id,
                         'account_receivable': party_configurations.account_receivable.id,
                         'type_': 'supplier',
                         'supplier_payment_term': supplier_payment_term,
                         'customer_payment_term': supplier_payment_term
                         }]
            party_party = party_partys.create(add_each)
            marks = int(party_party[0].id)
            party_addresss.create([{'party': marks,
                                    'street': street,
                                    'name': code,
                                    'invoice': False,
                                    'delivery': delivery,
                                    'active': address_active}])
            value['mark'] = marks
        # if value['mark'] is not None:
        return super(New_party, cls).create(vlist)

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
        return super(New_party, cls).delete(records)


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
            if 'code' in values:
                lv['name'] = values['code']
                lvc['code'] = values['code']
            if 'party' in values:
                lv['party'] = values[mark]
            if 'street' in values:
                lv['street'] = values['street']
            if 'invoice' in values:
                lv['invoice'] = values['invoice']
            if 'deivery' in values:
                lv['delivery'] = values['deivery']
            if 'address_active' in values:
                lv['active'] = values['address_active']
            if lv != {}:
                party_addresss.write(party_address, lv)
            if 'name' in values:
                lvc['name'] = values['name']
            if 'active' in values:
                lvc['active'] = values['active']
            if 'supplier_payment_term' in values:
                lvc['supplier_payment_term'] = values['supplier_payment_term']
            if lvc != {}:
                party_partys.write(party_party, lvc)
        if values['mark'] is not None:
            return super(New_party, cls).write(records, values)
