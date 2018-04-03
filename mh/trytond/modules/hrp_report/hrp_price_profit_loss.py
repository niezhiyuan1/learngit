# coding:utf-8
from psycopg2._psycopg import cursor
from sql import Literal
from sql.aggregate import Max
from trytond.pool import Pool
from trytond.pyson import Eval, Equal, Bool, PYSONEncoder
from trytond.model import ModelView, fields, ModelSQL
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction
import sys

reload(sys)
sys.setdefaultencoding('utf8')

__all__ = ['PriceProfitLoss', 'PriceProfitLossMessage', 'PriceProfitLossWizard', 'PriceProfitLossContent']


class PriceProfitLossMessage(ModelSQL, ModelView):
    """Price Profit Loss Message"""

    __name__ = 'hrp_report.price_profit_loss_message'

    number = fields.Function(fields.Char('number', select=True), 'get_number')  # 编号
    code = fields.Function(fields.Char('code', select=True), 'get_code')  # 编码
    product = fields.Function(fields.Char('product', select=True), 'get_product')  # 药品名称
    drug_specifications = fields.Function(fields.Char('drug_specifications', select=True),
                                          'get_drug_specifications')  # 规格
    list_price = fields.Function(fields.Numeric('list_price', select=True, digits=(16, 4)), 'get_list_price')
    cost_price = fields.Function(fields.Numeric('cost_price', select=True, digits=(16, 4)), 'get_cost_price')
    new_list_price = fields.Function(fields.Float('new_list_price', select=True, digits=(16, 4)), 'get_new_list_price')
    new_cost_price = fields.Function(fields.Float('new_cost_price', select=True, digits=(16, 4)), 'get_new_cost_price')
    uom = fields.Many2One('product.uom', 'uom', select=True)  # 单位
    inventory = fields.Function(fields.Float('inventory', select=True), 'get_inventory')  # 库存数量
    party = fields.Function(fields.Char('party', select=True), 'get_party')  # 库存数量
    price_profit_loss = fields.Function(fields.Numeric('price_profit_loss', select=True),
                                        'get_price_profit_loss')  # 批发盈亏金额
    price_list_profit_loss = fields.Function(fields.Numeric('price_list_profit_loss', select=True),
                                             'get_price_list_profit_loss')  # 零售盈亏金额
    effective_date = fields.Function(fields.Date('effective_date', select=True), 'get_effective_date')  # 生效日期

    @staticmethod
    def table_query(self=None):
        price_profit_loss = Pool().get('hrp_report.price_profit_loss_content')
        ProfitLoss = price_profit_loss.__table__()
        where = Literal(True)
        condition = []
        if Transaction().context.get('location') != None:
            condition.append(('location', '=', Transaction().context.get('location')))
        if Transaction().context.get('start_time') != None:
            condition.append(('effective_date', '>=', Transaction().context.get('start_time')))
        if Transaction().context.get('end_time') != None:
            condition.append(('effective_date', '<=', Transaction().context.get('end_time')))
        if Transaction().context.get('drug_type') != None:
            if Transaction().context.get('drug_type') == '06':
                pass
            else:
                condition.append(('drug_type', '=', Transaction().context.get('drug_type')))

        product_ids = price_profit_loss.search([condition], query=True, order=[])
        where &= ProfitLoss.id.in_(product_ids)
        Result = ProfitLoss.select(
            ProfitLoss.id.as_('id'),
            Max(ProfitLoss.create_uid).as_('create_uid'),
            Max(ProfitLoss.create_date).as_('create_date'),
            Max(ProfitLoss.write_uid).as_('write_uid'),
            Max(ProfitLoss.write_date).as_('write_date'),
            ProfitLoss.uom,
            where=where,
            group_by=ProfitLoss.id)
        return Result

    def get_number(self, name):
        price_profit_loss = Pool().get('hrp_report.price_profit_loss_content')
        condition = []
        if Transaction().context.get('location') != None:
            condition.append(('location', '=', Transaction().context.get('location')))
        if Transaction().context.get('start_time') != None:
            condition.append(('effective_date', '>=', Transaction().context.get('start_time')))
        if Transaction().context.get('end_time') != None:
            condition.append(('effective_date', '<=', Transaction().context.get('end_time')))
        if Transaction().context.get('drug_type') != None:
            if Transaction().context.get('drug_type') == '06':
                pass
            else:
                condition.append(('drug_type', '=', Transaction().context.get('drug_type')))

        product_ids = price_profit_loss.search([condition])
        list_id = []
        for each in product_ids:
            list_id.append(each.id)
        num = 0
        for i in list_id:
            num += 1
            if i == self.id:
                break
        return num

    def get_code(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        code = price_list.code
        return code

    def get_party(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        party = price_list.party
        return party

    def get_product(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        product = price_list.product
        return product

    def get_drug_specifications(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        drug_specifications = price_list.drug_specifications
        return drug_specifications

    def get_list_price(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        list_price = price_list.list_price
        return list_price

    def get_cost_price(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        cost_price = price_list.cost_price
        return cost_price

    def get_new_list_price(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        new_list_price = price_list.new_list_price
        return new_list_price

    def get_new_cost_price(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        new_cost_price = price_list.new_cost_price
        return new_cost_price

    def get_effective_date(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        effective_date = price_list.effective_date
        return effective_date

    def get_price_profit_loss(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        price_profit_loss = price_list.price_profit_loss
        return price_profit_loss

    def get_price_list_profit_loss(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        price_list_profit_loss = price_list.price_list_profit_loss
        return price_list_profit_loss

    def get_inventory(self, name):
        Price = Pool().get('hrp_report.price_profit_loss_content')
        price_list = Price(self.id)
        inventory = price_list.inventory
        return inventory


class PriceProfitLoss(ModelView):
    """Price Profit Loss"""
    __name__ = 'hrp_report.price_profit_loss'

    location = fields.Many2One('stock.location', 'location', select=True, required=True, depends=['location_id'],
                               domain=[('id', 'in', Eval('location_id'))])  # 部门
    location_id = fields.Function(fields.One2Many('stock.location', 'None', 'location_id'),
                                  'on_change_with_location_id')
    start_time = fields.Date('start_time', select=True)  # 开始时间
    end_time = fields.Date('end_time', select=True)  # 结束时间
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
    moves = fields.One2Many('hrp_report.price_profit_loss_message', 'None', 'moves')  # 显示界面

    @fields.depends('location_id')
    def on_change_with_location_id(self, name=None):
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_all_warehouse()

    @staticmethod
    def default_location_id():
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        return [config.hospital.id, config.outpatient_service.id, config.warehouse.id, config.medical.id,
                config.endoscopic.id, config.preparation.id, config.ward.id, config.herbs.id]

    @staticmethod
    def default_start_time():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

    @staticmethod
    def default_end_time():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today


class PriceProfitLossWizard(Wizard):
    """Price Profit Loss Wizard"""
    __name__ = 'hrp_report.price_profit_loss_wizard'

    start = StateView('hrp_report.price_profit_loss',
                      'hrp_report.hrp_price_profit_loss_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Open', 'report', 'tryton-ok', default=True),
                      ])
    report = StateAction('hrp_report.act_hrp_price_profit_loss_message')

    def do_report(self, action):
        dict = {}
        try:
            self.start.location.id
            dict['location'] = self.start.location.id
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
            self.start.drug_type
            dict['drug_type'] = self.start.drug_type
        except:
            pass

        action['pyson_context'] = PYSONEncoder().encode(dict)

        action['name'] += ' - (%s) @ %s' % (u'调价盈亏报表', self.start.start_time)
        return action, {}


class PriceProfitLossContent(ModelSQL, ModelView):
    """Price Profit Loss Message Content"""
    __name__ = 'hrp_report.price_profit_loss_content'

    location = fields.Many2One('stock.location', 'location', select=True)  # 库存地
    number = fields.Char('number', select=True)  # 编号
    code = fields.Char('code', select=True)  # 编码
    product = fields.Char('product', select=True)  # 药品名称
    drug_specifications = fields.Char('drug_specifications', select=True)  # 规格
    list_price = fields.Numeric('list_price', select=True, digits=(16, 4))
    cost_price = fields.Numeric('cost_price', select=True, digits=(16, 4))
    new_list_price = fields.Float('new_list_price', select=True, digits=(16, 4))
    new_cost_price = fields.Float('new_cost_price', select=True, digits=(16, 4))
    uom = fields.Many2One('product.uom', 'uom', select=True)  # 单位
    inventory = fields.Float('inventory', select=True)  # 库存数量
    price_profit_loss = fields.Numeric('price_profit_loss', select=True)  # 批发盈亏金额
    price_list_profit_loss = fields.Numeric('price_list_profit_loss', select=True)  # 零售盈亏金额
    effective_date = fields.Date('effective_date', select=True)  # 生效日期
    party = fields.Char('party', select=True)  # 供应商
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素'),
    ], 'drug_type', select=True)  # 药品类型






    # cursor.execute("SELECT cl2.relname "
    #
    #                 "FROM pg_index ind "
    #
    #                 "JOIN pg_class cl on (cl.oid = ind.indrelid) "
    #
    #                 "JOIN pg_namespace n ON (cl.relnamespace = n.oid) "
    #
    #                 "JOIN pg_class cl2 on (cl2.oid = ind.indexrelid) "
    #
    #                 "WHERE cl.relname = %s AND n.nspname = %s",
    #
    #             (self.table_name, self.))table_schema