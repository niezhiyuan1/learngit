# coding:utf-8
from sql import Literal
from sql.aggregate import Max
from trytond.pool import Pool
from trytond.pyson import Eval, Equal, Bool, PYSONEncoder
from trytond.model import ModelView, fields, ModelSQL
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['PriceAdjustment', 'PriceAdjustmentMessage', 'PriceAdjustmentWizard']


class PriceAdjustment(ModelView):
    """Price Adjustment"""
    __name__ = 'hrp_report.price_adjustment'

    type = fields.Selection([
        ('00', u'时间'),
        ('01', u'药品简码'),
    ], 'type', select=True, states={
        'readonly': Bool(Eval('moves')),
    })  # 查询类型
    drug_code = fields.Many2One('product.product', 'drug_code', select=True, states={
        'readonly': ~Equal(Eval('type'), '01')
    }, depends=['type'])  # 药品简码
    start_time = fields.Date('start_time', select=True, states={
        'readonly': ~Equal(Eval('type'), '00')
    }, depends=['type'])  # 开始时间
    end_time = fields.Date('end_time', select=True, states={
        'readonly': ~Equal(Eval('type'), '00')
    }, depends=['type'])  # 结束时间
    find = fields.Boolean('find', select=True)  # 查找按钮
    moves = fields.One2Many('hrp_report.price_adjustment_message', 'None', 'moves')  # 显示界面

    @fields.depends('type', 'start_time', 'start_time', 'drug_code')
    def on_change_type(self):
        if self.type == '00':
            Date = Pool().get('ir.date')
            today = str(Date.today())
            self.start_time = today
            self.end_time = today
            self.drug_code = None
        else:
            self.start_time = None
            self.end_time = None

    @staticmethod
    def default_type():
        return '00'


class PriceAdjustmentWizard(Wizard):
    """Price Adjustment Wizard"""
    __name__ = 'hrp_report.price_adjustment_wizard'

    start = StateView('hrp_report.price_adjustment',
                      'hrp_report.hrp_price_adjustment_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Open', 'report', 'tryton-ok', default=True),
                      ])
    report = StateAction('hrp_report.act_hrp_price_adjustment_message')

    def do_report(self, action):
        dict = {}

        try:
            self.start.type
            dict['type'] = self.start.type
        except:
            pass
        try:
            self.start.drug_code.id
            dict['drug_code'] = self.start.drug_code.id
        except:
            pass
        try:
            self.start.start_time
            dict['start_time'] = self.start.start_time
        except:
            pass
        try:
            self.start.end_time
            dict['end_time'] = self.start.end_time
        except:
            pass

        try:
            action['pyson_context'] = PYSONEncoder().encode(dict)
        except:
            pass
        action['name'] += ' - (%s) @ %s' % (u'调价报表', self.start.start_time)
        return action, {}


class PriceAdjustmentMessage(ModelSQL, ModelView):
    """Price Adjustment Message"""
    __name__ = 'hrp_report.price_adjustment_message'

    code = fields.Function(fields.Char('code', select=True), 'get_code')  # 编码
    product = fields.Function(fields.Char('product', select=True), 'get_product')  # 药品名称
    drug_specifications = fields.Char('drug_specifications', select=True)  # 规格
    list_price = fields.Function(fields.Numeric('list_price', select=True, digits=(16, 4)), 'get_list_price')
    cost_price = fields.Function(fields.Numeric('cost_price', select=True, digits=(16, 4)), 'get_cost_price')
    new_list_price = fields.Function(fields.Float('new_list_price', select=True, digits=(16, 4)), 'get_new_list_price')
    new_cost_price = fields.Function(fields.Float('new_cost_price', select=True, digits=(16, 4)), 'get_new_cost_price')
    effective_date = fields.Function(fields.Date('effective_date', select=True), 'get_effective_date')  # 生效日期
    modify_reason = fields.Function(fields.Selection([
        ('00', u'来药单'),
        ('01', u'海虹药通'),
    ], 'modify_reason', select=True), 'get_modify_reason')  # 调价原因

    @staticmethod
    def table_query(self=None):
        price_list = Pool().get('price_master_datas.pricedata')
        PriceList = price_list.__table__()
        where = Literal(False)
        if Transaction().context.get('type') == '01':
            Product = Pool().get('product.product')
            drug_code = Transaction().context.get('drug_code')
            product_id = Product.search([('id', '=', drug_code)])
            if product_id != []:
                where = Literal(True)
                product_id_price = product_id[0].id
                Price = price_list.search([('retrieve_the_code', '=', product_id_price)], query=True, order=[])
                where &= PriceList.id.in_(Price)
        if Transaction().context.get('type') == '00':
            condition = []
            start_time = Transaction().context.get('start_time')
            end_time = Transaction().context.get('end_time')
            if start_time != None:
                condition.append(('effective_date', '>=', start_time), )
            if end_time != None:
                condition.append(('effective_date', '<=', end_time), )
            Price = price_list.search(condition)
            if Price != []:
                price_id = []
                where = Literal(True)
                for i in Price:
                    price_id.append(i.id)
                where &= PriceList.id.in_(price_id)
        Result = PriceList.select(
            PriceList.id.as_('id'),
            Max(PriceList.create_uid).as_('create_uid'),
            Max(PriceList.create_date).as_('create_date'),
            Max(PriceList.write_uid).as_('write_uid'),
            Max(PriceList.write_date).as_('write_date'),
            PriceList.drug_specifications.as_('drug_specifications'),
            where=where,
            group_by=PriceList.id)
        return Result

    def get_code(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        code = price_list.retrieve_the_code.code
        return code

    def get_product(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        product = price_list.retrieve_the_code.name
        return product

    def get_list_price(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        list_price = price_list.list_price
        return list_price

    def get_cost_price(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        cost_price = price_list.cost_price
        return cost_price

    def get_new_list_price(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        new_list_price = price_list.new_list_price
        return new_list_price

    def get_new_cost_price(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        new_cost_price = price_list.new_cost_price
        return new_cost_price

    def get_effective_date(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        effective_date = price_list.effective_date
        return effective_date

    def get_modify_reason(self, name):
        Price = Pool().get('price_master_datas.pricedata')
        price_list = Price(self.id)
        modify_reason = price_list.modify_reason
        return modify_reason
