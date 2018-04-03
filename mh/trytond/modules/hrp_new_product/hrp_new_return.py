# coding:utf-8
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import StateView

__all__ = ['NewReturn']


class NewReturn(ModelSQL, ModelView):
    'New Product'
    __name__ = 'hrp_new_product.new_return'

    product = fields.Many2One("product.product", "Product", required=True)  # 产品

    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素'),
    ], 'Starts', select=True)  # 药品类型

    date_from = fields.Date('date_from', select=True)  # 有效期范围
    date_to = fields.Date('date_to', select=True)  #
    retrieve_the_code = fields.Char('retrieve_the_code', select=True)  # 拼音简码
    from_location = fields.Many2One("stock.location", "from_location", select=True)  # 仓库存储
    to_location = fields.Many2One("stock.location", "to_location", select=True)  # 仓库存储
    code = fields.Char('code', select=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True)  # 单位
    return_quantity = fields.Integer('Return Quantity', select=True)  # 清退数量
    lot = fields.Many2One('stock.lot', 'Lot')  # 药品批次
    reason = fields.Selection([
        ('00', u''),
        ('01', u'药品过期'),
        ('02', u'无外标签'),
        ('03', u'原装破损'),
        ('04', u'科室自用'),
        ('05', u'近期药品'),
        ('06', u'长期不用'),
        ('07', u'停药'),
        ('08', u'病人退药'),
        ('09', u'工作失误'),
        ('10', u'单据错误'),
    ], 'Reason', select=True)  # 退药原因
    comment = fields.Text('Comment', select=True)  # 备注

    can_return_quantity = fields.Float('Can Return Quantity', select=True)  # 可以退的药品数量

    examine = fields.Selection([
        ('00', u''),
        ('01', u'未审核'),
        ('02', u'已审核'),
    ], 'Examine', select=True)  # 退药审核

    is_direct_sending = fields.Boolean('Is_direct_sending', select=True)  # 是否直送

    @staticmethod
    def default_reason():
        return '00'

    @staticmethod
    def default_examine():
        return '00'

    @staticmethod
    def default_drug_type():
        return '06'

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
                ('retrieve_the_code',) + tuple(clause[1:]),
                ('product.template.name',) + tuple(clause[1:]),
                ]

    @classmethod
    def do_open(self):
        pool = Pool()
        UomCategory = Pool().get('product.category')
        Hrp_Order = Pool().get('hrp_order_point.purchaser_reference')
        OrderPoint = pool.get('stock.order_point')
        PurchaseNewProduct = pool.get("hrp_new_product.new_product")
        orderpoints = OrderPoint.search([
            ('type', '=', 'internal')
        ])
        Date = Pool().get('ir.date')
        Product = pool.get('product.product')
        delete_move = PurchaseNewProduct.search([])
        PurchaseNewProduct.delete(delete_move)
        for orderpoint in orderpoints:
            order_product_id = []  # 订货点产品id
            try:
                party = orderpoint.product.template.product_suppliers[0].party.id
            except:
                party = None
            unit_price = orderpoint.product.cost_price
            warehouse_location = orderpoint.warehouse_location
            retrieve_the_code = orderpoint.retrieve_the_code
            secondary = orderpoint.secondary
            storage_location = orderpoint.provisioning_location.id  # 来自库存低
            provisioning_location = orderpoint.storage_location.id  # 到达库存地
            product = orderpoint.product.id  # 产品
            interim = orderpoint.product.interim  # 产品
            hrp_order = Hrp_Order.search([
                ('warehouse', '=', secondary),
                ('product', '=', product),
            ])
            if hrp_order:
                seven_days = hrp_order[0].seven_days
            else:
                seven_days = 0
            purchase_new = OrderPoint.search([
                ('storage_location', '=', provisioning_location),
            ])
            if purchase_new:
                for i in purchase_new:
                    order_product_id.append(i.product.id)
            categories = [i.id for i in orderpoint.product.categories]
            uom_category = UomCategory.search([('id', '=', categories[0])])
            uom_name = uom_category[0].name

            code = orderpoint.product.code  # 编码
            drug_specifications = orderpoint.product.drug_specifications  # 规格
            a_charge = orderpoint.product.template.a_charge  # 件装量
            is_direct_sending = orderpoint.product.template.is_direct_sending  # 直送
            unit = orderpoint.unit.id  # 单位
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                quantities = Product.products_by_location([provisioning_location], [product], with_childs=True)
            if quantities.values():
                stock_level = [v for v in quantities.values()][0]
            else:
                stock_level = 0
            proposal = seven_days - stock_level
            lv = {}
            lv['drug_specifications'] = drug_specifications
            lv['stock_level'] = int(stock_level)
            lv['warehouse_location'] = warehouse_location
            if uom_name == u'中成药':
                lv['drug_type'] = '01'
            if uom_name == u'中草药':
                lv['drug_type'] = '02'
            if uom_name == u'原料药':
                lv['drug_type'] = '04'
            if uom_name == u'敷药':
                lv['drug_type'] = '05'
            if uom_name == u'西药':
                lv['drug_type'] = '00'
            if uom_name == u'颗粒中':
                lv['drug_type'] = '03'
            if uom_name == u'同位素':
                lv['drug_type'] = '07'
            if uom_name == '':
                lv['drug_type'] = '06'
            lv['product'] = product
            lv['code'] = code
            if a_charge == None:
                lv['a_charge'] = ''
            else:
                lv['a_charge'] = str(a_charge)
            lv['from_location'] = storage_location
            lv['retrieve_the_code'] = str(retrieve_the_code)
            lv['to_location'] = provisioning_location
            lv['is_direct_sending'] = is_direct_sending
            lv['unit_price'] = unit_price
            lv['uom'] = unit
            lv['outpatient_7days'] = seven_days
            lv['party'] = party  # 供应商
            lv['proposal'] = proposal  # 建议采购量
            if interim == '1' or '00':
                lv['interim'] = '1'
            elif interim == '01':
                lv['interim'] == '2'
            else:
                lv['interim'] = interim
            PurchaseNew = PurchaseNewProduct.search([
                ('to_location', '=', provisioning_location),
                ('product', '=', product)
            ])
            if PurchaseNew:
                PurchaseNewProduct.write(PurchaseNew, lv)
            else:
                PurchaseNewProduct.create([lv])
