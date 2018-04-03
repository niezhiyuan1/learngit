# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from sql.aggregate import Max
from sql import Literal, Join
from trytond.pyson import If, Equal, Eval, Not, In, Bool
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.config import config

__all__ = ['AvailableMedicine', 'AvailableMedicineLine', 'ShelvesName']

price_digits = (16, config.getint('product', 'price_decimal', default=2))


class AvailableMedicine(ModelSQL, ModelView):
    "AvailableMedicine"
    __name__ = "hrp_inventory.available_medicine"

    warehouse = fields.Many2One('stock.location', 'Warehouse', domain=[('type', '=', 'warehouse')], select=True)
    varieties_num = fields.Integer('Varieties Num', readonly=True)
    lines = fields.One2Many('hrp_inventory.available_medicine_line', 'available_medicine', 'Lines')

    @classmethod
    def __setup__(cls):
        super(AvailableMedicine, cls).__setup__()
        cls._buttons.update({
            'create_the_inventory': {
                'readonly': Eval('lines') != '',
            },
        })

    @classmethod
    @ModelView.button
    def create_the_inventory(self, available_medicine):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        AvailableMedicineLine = Pool().get('hrp_inventory.available_medicine_line')
        with Transaction().set_context(stock_date_end=Date.today()):
            warehouse_pbl = Product.products_by_location([available_medicine[0].warehouse.storage_location],
                                                         with_childs=True)
            lines = 0
            for key, value in warehouse_pbl.iteritems():
                lines += 1
                product = Product.search([('id', '=', key[1])])
                if not product:
                    continue
                to_create = {
                    u'lines': lines,
                    u'available_medicine': available_medicine[0].id,
                    u'product': product[0].id,
                    u'product_code': product[0].code.encode('utf-8'),
                    u'product_name': product[0].template.name.encode('utf-8'),
                    u'scattered_uom': product[0].default_uom.id,
                    u'manufacturers_code': product[0].template.manufacturers_code.encode('utf-8'),
                    u'manufacturers': product[0].template.manufacturers_describtion.encode('utf-8'),
                    u'drug_specifications': product[0].template.drug_specifications,
                }
                AvailableMedicineLine.create([to_create])
            AvailableMedicine.write(available_medicine, {'varieties_num': lines})


class ShelvesName(ModelSQL, ModelView):
    "ShelvesName"
    __name__ = "hrp_inventory.shelves_code"

    name = fields.Char('shelves_code', select=True)


class AvailableMedicineLine(ModelSQL, ModelView):
    "AvailableMedicineLine"
    __name__ = "hrp_inventory.available_medicine_line"

    shelves_code = fields.Char('shelves_code', select=True, readonly=True, required=False)
    new_shelves_code = fields.Char('new_shelves_code', select=True, readonly=False, required=False)
    warehouse = fields.Many2One('stock.location', 'Warehouse', domain=[('type', '=', 'warehouse')], select=True)
    product_code = fields.Function(fields.Char('product_code', readonly=True, required=False), 'get_product_code')
    product_name = fields.Function(fields.Char('product_name', readonly=True, required=False), 'get_product_name')
    product = fields.Many2One('product.product', 'Product', domain=[
        ('id', 'in', Eval('product_ids'))], depends=['product_ids'], select=True,
                              states={'readonly': Bool(Eval('product'))})
    product_ids = fields.Function(fields.One2Many('product.product', None, 'Products'), 'on_change_with_product_ids')
    safety_stock = fields.Integer('Safety stock', required=False)
    scattered_uom = fields.Many2One('product.uom', 'Default UOM', domain=[
        ('category', '=', Eval('product_uom_category'))], required=False, depends=['product_uom_category'])
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    drug_specifications = fields.Function(fields.Char('Drug Speic', readonly=True, required=False),
                                          'get_drug_specifications')
    manufacturers_code = fields.Function(fields.Char('Manufacturers_code', readonly=True, required=False),
                                         'get_manufacturers_code')
    manufacturers = fields.Function(fields.Char('Manufacturers', select=True, readonly=True, required=False),
                                    'get_manufacturers')

    @staticmethod
    def default_warehouse():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_warehouse()

    def get_product_code(self, name):

        Product = Pool().get('product.product')
        try:
            product = Product.search([('id', '=', self.product.id)])
            product_code = product[0].code.encode('utf-8')
        except:
            return None
        return product_code

    def get_product_name(self, name):

        Product = Pool().get('product.product')
        try:
            product = Product.search([('id', '=', self.product.id)])
            product_name = product[0].name.encode('utf-8')
        except:
            return None
        return product_name

    def get_drug_specifications(self, name):

        Product = Pool().get('product.product')
        try:
            product = Product.search([('id', '=', self.product.id)])
            drug_specifications = product[0].drug_specifications
        except:
            return None
        return drug_specifications

    def get_manufacturers_code(self, name):

        Product = Pool().get('product.product')
        try:
            product = Product.search([('id', '=', self.product.id)])
            manufacturers_code = product[0].manufacturers_code.encode('utf-8')
        except:
            return None
        return manufacturers_code

    def get_manufacturers(self, name):

        Product = Pool().get('product.product')
        try:
            product = Product.search([('id', '=', self.product.id)])
            manufacturers = product[0].manufacturers_describtion.encode('utf-8')
        except:
            return None
        return manufacturers

    @fields.depends('warehouse')
    def on_change_with_product_ids(self, name=None):
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        OrderPoint = Pool().get('stock.order_point')
        if self.warehouse == config.warehouse.id:
            order_point = OrderPoint.search([('warehouse_location', '=', self.warehouse)])
        else:
            order_point = OrderPoint.search([('secondary', '=', self.warehouse)])
        product_ids = []
        for ids in order_point:
            product_ids.append(ids.product.id)
        return product_ids

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('product', 'product_code', 'product_name', 'scattered_uom', 'drug_specifications',
                    'manufacturers_code', 'manufacturers')
    def on_change_product(self, name=None):
        if self.product:
            self.product_code = self.product.code
            self.product_name = self.product.name
            self.scattered_uom = self.product.template.default_uom
            self.drug_specifications = self.product.template.drug_specifications
            self.manufacturers_code = self.product.template.manufacturers_code
            self.manufacturers = self.product.template.manufacturers_describtion

    @classmethod
    def write(cls, records, values, *args):
        for i in records:
            try:
                values['shelves_code'] = values['new_shelves_code']
                values.pop('new_shelves_code')
            except:
                pass
        return super(AvailableMedicineLine, cls).write(records, values)

    @classmethod
    def create(cls, vlist):
        Product = Pool().get('product.product')
        ShelvesName = Pool().get('hrp_inventory.shelves_code')
        for value in vlist:
            if value['product'] and value['warehouse']:
                availble = AvailableMedicineLine.search([('product', '=', value['product']),
                                                         ('warehouse', '=', value['warehouse'])])
            if value['product']:
                product = Product.search([('id', '=', value['product'])])
                value['scattered_uom'] = product[0].template.default_uom.id

            if value['new_shelves_code']:
                shelves_code = ShelvesName.search([('name', '=', value['new_shelves_code'])])
                if not shelves_code:
                    ShelvesName.create([{'name': value['new_shelves_code']}])
            if not availble:
                try:
                    value['shelves_code'] = value['new_shelves_code']
                    value.pop('new_shelves_code')
                except:
                    pass
            else:
                cls.raise_user_error(u'该表中药品必须唯一,标识为:%s' % availble[0].id)
        return super(AvailableMedicineLine, cls).create(vlist)
