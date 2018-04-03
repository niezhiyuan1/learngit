# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.rpc import RPC
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.config import config
from trytond.transaction import Transaction

__all__ = ['ProductQuantity', 'Interfaceq']

price_digits = (16, config.getint('product', 'price_decimal', default=2))


class Interfaceq(ModelView, ModelSQL):
    'Interface'
    __name__ = "wms.interface"

    @classmethod
    def __setup__(cls):
        super(Interfaceq, cls).__setup__()
        cls.__rpc__.update({
            'search_n': RPC(readonly=False, check_access=False)})

    @classmethod
    def search_n(cls, regclass):
        return {"success": 'true', "message": regclass}


class ProductQuantity(ModelSQL, ModelView):
    'Product Quantity'
    __name__ = 'product_quantity'

    product_code = fields.Char('product_code', readonly=True, required=False)
    product_name = fields.Char('product_name', readonly=True, required=False)
    product = fields.Many2One('product.product', 'Product',
                              domain=[
                                  ('id', 'in', Eval('products')),
                              ], depends=['products', 'categories'])
    products = fields.Function(
        fields.One2Many('product.product', None, 'Products'),
        'on_change_with_products')
    categories = fields.Many2One('product.category', 'Categories', select=True)
    drug_specifications = fields.Function(fields.Char('Drug_specifications', select=True, readonly=True),
                                          'get_drug_specifications')
    default_uom = fields.Function(fields.Many2One('product.uom', 'Default UOM', required=False, readonly=True
                                                  ), 'get_default_uom')
    location = fields.Many2One('stock.location', 'location',
                               domain=[('is_goods', '=', True)], required=False, select=True)

    quantity = fields.Float('quantity', required=True)

    sequence = fields.Integer('sequence', select=True, required=True)

    additional = fields.Char('additional')

    @classmethod
    def create(cls, vlist):
        for value in vlist:
            product_quantity1 = ProductQuantity.search([('product', '=', value['product']),
                                                        ('sequence', '=', value['sequence'])])
            product_quantity2 = ProductQuantity.search([('product', '=', value['product']),
                                                        ('location', '=', value['location'])])
            if product_quantity1:
                cls.raise_user_error(u'该药品存在相同的优先级，请核对！')
            if product_quantity2:
                cls.raise_user_error(u'该药品已经存在相同货位号')
            Product = Pool().get('product.product')
            product = Product.search([('id', '=', value['product'])])
            value['additional'] = product[0].attach
            value['product_code'] = product[0].code
            value['product_name'] = product[0].name
        return super(ProductQuantity, cls).create(vlist)

    @classmethod
    def delete(cls, records):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        for values in records:
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([warehouse], with_childs=True, grouping=('product', 'lot'))
                ids = []
                for key, value in pbl.items():
                    if value > 0 and key[1] is not None:
                        ids.append(key[1])
            if values.product.id in ids:
                cls.raise_user_error(u'该条数据下已有库存记录，不允许删除')
            else:
                return super(ProductQuantity, cls).delete(records)

    @classmethod
    def write(cls, records, values, *args):
        Product = Pool().get('product.product')
        if 'product' in values:
            values['product_code'] = Product(values['product']).code
            values['product_name'] = Product(values['product']).name
        return super(ProductQuantity, cls).write(records, values)

    @fields.depends('product', 'default_uom', 'drug_specifications', 'product_code', 'product_name', 'additional')
    def on_change_product(self, name=None):
        if self.product:
            Product = Pool().get('product.product')
            product = Product.search([('id', '=', self.product.id)])
            self.default_uom = product[0].default_uom
            self.drug_specifications = product[0].drug_specifications
            self.product_code = product[0].code
            self.product_name = product[0].name
            self.additional = product[0].attach

    @fields.depends('categories', 'products')
    def on_change_with_products(self, name=None):
        if self.categories:
            Template = Pool().get('product.template')
            UomCategory = Pool().get('product.category')
            category = UomCategory.search([('name', '=', self.categories.name)])
            product = Template.search([('categories', 'in', [category[0].id])])
            product_ids = []
            for i in product:
                product_ids.append(i.products[0].id)
            return product_ids

    def get_default_uom(self, name):  ###
        return self.product.template.default_uom.id

    def get_drug_specifications(self, name):
        return self.product.template.drug_specifications
