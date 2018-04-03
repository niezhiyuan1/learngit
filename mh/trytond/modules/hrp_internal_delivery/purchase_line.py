# coding:utf-8
from trytond.model import fields
from trytond.pool import PoolMeta, Pool

__all__ = ['PurchaseLine']


class PurchaseLine:
    __metaclass__ = PoolMeta
    __name__ = "purchase.line"

    code = fields.Function(fields.Char('code', select=True), 'get_code')  # 编码

    drug_starts = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u''),
        ('07', u'同位素'),
    ], 'drug_starts', select=True)

    internal_order = fields.Char('internal_order', select=True, readonly=True)  #

    @staticmethod
    def default_drug_starts():
        return '06'

    def get_code(self, name):
        pool = Pool()
        try:
            product_products = pool.get('product.product')
            product_product = product_products.search([
                ("id", "=", int(self.product.id))
            ])
            get_code = product_product[0].code
        except:
            return None
        return get_code
