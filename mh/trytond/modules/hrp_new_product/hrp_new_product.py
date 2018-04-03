# coding:utf-8
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['NewProduct']


class NewProduct(ModelSQL, ModelView):
    """New Product"""

    __name__ = 'hrp_new_product.new_product'

    warehouse_location = fields.Many2One("stock.location", "warehouse_location", select=True)  # 仓库存储

    from_location = fields.Many2One("stock.location", "from_location", select=True)  # 仓库存储
    to_location = fields.Many2One("stock.location", "to_location", select=True)  # 仓库存储
    product = fields.Many2One("product.product", "Product", required=True)  # 产品
    code = fields.Char('code', select=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True)  # 规格
    uom = fields.Many2One('product.uom', 'uom', select=True)  # 单位
    odd_numbers = fields.Char('odd_numbers', select=True)  # 单号
    a_charge = fields.Char('a_charge', select=True)  # 件装量
    stock_level = fields.Integer('stock_level', select=True)  # 现有库存量
    outpatient_7days = fields.Integer('Outpatient_7days', select=True, readonly=True)  # 7日量
    proposal = fields.Integer('proposal', select=True)  # 建议请领量
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True)  # 是否直送
    lot = fields.Many2One('stock.lot', 'Lot')  # 药品批次
    is_collar = fields.Boolean('is_collar', select=True)  # 是否请领
    befor_number = fields.Char('befor_number', select=True)  # 实发数量
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素')
    ], 'drug_type', select=True)  # 药品类型
    retrieve_the_code = fields.Char('retrieve_the_code', select=True)  # 拼音简码
    party = fields.Many2One('party.party', 'Party', select=True)  # 供应商
    unit_price = fields.Numeric('unit_price', digits=(16, 4))  # 价格
    interim = fields.Selection([
        ('1', u''),
        ('02', u'精一'),
        ('03', u'麻醉'),
        ('2', u'临采 '),
    ], 'interim', select=True)  # 是否临采

    @staticmethod
    def default_drug_type():
        return '06'
