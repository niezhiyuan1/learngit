# coding:utf-8
import decimal

from sql import Literal, Join, Null
from sql.aggregate import Max
from sql.functions import CurrentTimestamp
from sql.conditionals import Coalesce
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, PYSONEncoder, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction, StateTransition

__all__ = ['InventoryReport', 'InventoryReportConditionsStart', 'InventoryReportConditionsWizard',
           'StockInventoryReportWizard', 'StockInventoryReportStart', 'StockInventoryReport',
           'StockShipmentOrderReport',
           'StockShipmentReportStart', 'StockShipmentOrderInReport', 'StockShipmentInvoiceReport',
           'StockShipmentReportWizard', 'StockShipmentCategoryReport']


class InventoryReport(ModelSQL, ModelView):
    """InventoryReport"""
    __name__ = "hrp_inventory_report.inventory_report"

    code = fields.Char('code', select=True)  # 编码
    product = fields.Many2One('product.product', 'product', select=True)  # 药品名称
    name = fields.Char('name', select=True)  # 药品名称
    drug_specifications = fields.Char('drug_specifications', select=True)  # 规格
    quantity = fields.Function(fields.Float('quantity', digits=(16, 2), select=True, readonly=True),
                               'get_wholesale_amount')  # 数量
    uom = fields.Many2One('product.uom', 'Default UOM', select=True, left=True)  # 单位
    cost_pice = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)  # 单价
    wholesale_amount = fields.Function(fields.Numeric('Wholesale amount', readonly=True, digits=(16, 2)),
                                       'get_wholesale_amount')  # 金额
    differences_why = fields.Selection([('00', u''), ('01', u'少发'), ('02', u'科室结余'), ('03', u'半片医嘱'),
                                        ('04', u'发混'), ('05', u'盘点偏差'), ('06', u'原因不明，重点监控'), ('07', u'相似药品差错'),
                                        ('08', u'患者遗漏'), ('09', u'患者未取药，电脑误确'), ('10', u'多发'),
                                        ('11', u'发药未及时确认')], 'Differences Why', required=False)
    type = fields.Selection([
        ('0', ''),
        ('surplus', u'盘盈'),
        ('shortages', u'盘亏'),
        ('balance', u'平衡')
    ], 'Type', readonly=True)

    @staticmethod
    def table_query():
        pool = Pool()
        inventory_two = pool.get('hrp_inventory.inventory_two').__table__()
        inventory_lines = pool.get('hrp_inventory.inventory_two_lines').__table__()
        join1 = Join(inventory_lines, inventory_two)
        join1.condition = join1.right.id == inventory_lines.inventory
        where = Literal(True)
        if Transaction().context.get('inventor_time'):
            where &= inventory_two.id == Transaction().context['inventor_time']
            where &= inventory_lines.category == Transaction().context['category']
            where &= inventory_lines.type != 'balance'
        Result = join1.select(
            join1.left.id.as_('id'),
            Max(inventory_lines.create_uid).as_('create_uid'),
            Max(inventory_lines.create_date).as_('create_date'),
            Max(inventory_lines.write_uid).as_('write_uid'),
            Max(inventory_lines.write_date).as_('write_date'),
            inventory_lines.code,
            inventory_lines.uom,
            inventory_lines.name,
            inventory_lines.product,
            inventory_lines.drug_specifications,
            inventory_lines.cost_pice,
            inventory_lines.type,
            inventory_lines.differences_why,
            where=where,
            group_by=inventory_lines.id)
        return Result

    def get_wholesale_amount(self, name):
        pool = Pool()
        InventoryLines = pool.get('hrp_inventory.inventory_two_lines')
        inventory_lines = InventoryLines.search([('id', '=', self.id)])
        differences = inventory_lines[0].warehouse_real_num - inventory_lines[0].warehouse_num
        wholesale_amount = self.cost_pice * decimal.Decimal(str(differences)).quantize(decimal.Decimal('0.00'))
        if name == 'quantity':
            return differences
        if name == 'wholesale_amount':
            return wholesale_amount


class InventoryReportConditionsStart(ModelView):
    """InventoryReportConditions"""
    __name__ = 'hrp_inventrory_report.inventory_report_conditions_start'

    location = fields.Many2One('stock.location', 'location', select=True, required=True,
                               domain=[('type', '=', 'warehouse')],
                               states={'readonly': Bool(Eval('inventor_time'))}, depends=['inventor_time'])  # 库存地
    inventor_times = fields.Function(fields.One2Many('hrp_inventory.inventory_time', None, 'inventor_times'),
                                     'on_change_with_inventor_times')
    inventor_time = fields.Many2One('hrp_inventory.inventory_time', 'InventoryTime', select=True, required=True,
                                    domain=[('inventory', 'in', Eval('inventor_times'))],
                                    depends=['location', 'inventor_times', 'categories'])  # 批次
    category = fields.Many2One('product.category', 'Category', select=True, required=False)  # 药品类型

    @fields.depends('location', 'categories', 'inventor_time')
    def on_change_with_inventor_times(self, name=None):
        pool = Pool()
        InventoryTwo = pool.get('hrp_inventory.inventory_two')
        search = [('state', '=', 'done')]
        ids = []
        if self.location:
            search.append(('warehouse', '=', self.location.id))
        inventory_two = InventoryTwo.search(search)
        for i in inventory_two:
            ids.append(i.id)
        return ids


class InventoryReportConditionsWizard(Wizard):
    """InventoryReportConditions"""
    __name__ = 'hrp_inventory_report.inventory_report_conditions'

    start = StateView('hrp_inventrory_report.inventory_report_conditions_start',
                      'hrp_inventory_report.hrp_inventory_report_conditions_start_view_form', [
                          Button(u'取消', 'end', 'tryton-cancel'),
                          Button(u'打开', 'report', 'tryton-ok', default=True),
                      ])
    report = StateAction('hrp_inventory_report.act_hrp_inventory_report')

    def do_report(self, action):
        action['pyson_context'] = PYSONEncoder().encode({
            'inventor_time': self.start.inventor_time.inventory.id,
            'category': self.start.category.id
        })
        action['name'] += ' - (%s) @ %s' % (self.start.location.name, self.start.category.name)
        return action, {}


# 库存清点表


class StockInventoryReport(ModelSQL, ModelView):
    """StockInventoryReport"""
    __name__ = "hrp_inventory_report.stock_inventory_report"

    shelves_code = fields.Function(fields.Char('shelves_code', select=True, readonly=True, required=False),  # 货架编码
                                   'get_shelves_code')
    code = fields.Function(fields.Char('code', select=True), 'get_data')  # 编码
    name = fields.Function(fields.Char('name', select=True), 'get_data')  # 药品名称
    drug_specifications = fields.Function(fields.Char('drug_specifications', select=True),
                                          'get_data')  # 规格
    quantity = fields.Function(fields.Float('quantity', digits=(16, 2), select=True, readonly=True),
                               'get_quantity')  # 非限制数量
    freeze_quantity = fields.Function(fields.Float('freeze_quantity', digits=(16, 2), select=True, readonly=True),
                                      'get_quantity')  # 冻结数量
    scanning_quantity = fields.Function(fields.Float('scanning_quantity', digits=(16, 2), select=True, readonly=True),
                                        'get_quantity')  # 扫描数量
    uom = fields.Function(fields.Many2One('product.uom', 'Default UOM', select=True, left=True), 'get_data')  # 单位

    @staticmethod
    def table_query():

        pool = Pool()
        Date = pool.get('ir.date')
        Location = Pool().get('stock.location')
        Product = pool.get('product.product')
        Template = pool.get('product.template')
        AvailableMedicineLine = pool.get("hrp_inventory.available_medicine_line")
        template = pool.get('product.template').__table__()
        products = pool.get('product.product').__table__()
        available_medicine_line = pool.get('hrp_inventory.available_medicine_line').__table__()
        where = Literal(True)
        ids = []
        if Transaction().context.get('location') and Transaction().context.get('category'):
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location(
                    [Transaction().context['location'], Location(Transaction().context['location']).freeze_location.id],
                    with_childs=True)
                for key, value in pbl.items():
                    if value > 0 and key[1] is not None:
                        if Product(key[1]).template.categories[0].id == Transaction().context['category']:
                            ids.append(key[1])
                set(ids)
                where &= products.id.in_(ids)
                if not ids:
                    where = Literal(False)
        if Transaction().context.get('shelves_code'):
            ids2 = []
            lines = AvailableMedicineLine.search([('product', 'in', ids),
                                                  ('warehouse', '=', Transaction().context['location'])])
            for i in lines:
                ids2.append(i)
            jiao = [val for val in ids2 if val in ids]
            where &= products.id.in_(jiao)
        Result = products.select(
            products.id.as_('id'),
            Max(products.create_uid).as_('create_uid'),
            Max(products.create_date).as_('create_date'),
            Max(products.write_uid).as_('write_uid'),
            Max(products.write_date).as_('write_date'),
            where=where,
            group_by=products.id)
        return Result

    def get_data(self, name):
        pool = Pool()
        Product = pool.get('product.product')
        AvailableMedicineLine = pool.get("hrp_inventory.available_medicine_line")
        data = Product(self.id).template
        if name == 'uom':
            if Transaction().context.get('shelves_code'):
                lines = AvailableMedicineLine.search([('product', '=', self.id),
                                                      ('warehouse', '=', Transaction().context['location'])])
                return lines[0].scattered_uom.id
            return data.default_uom.id
        if name == 'code':
            return Product(self.id).code
        if name == 'drug_specifications':
            return data.drug_specifications
        if name == 'name':
            return data.name

    def get_shelves_code(self, name):
        if Transaction().context.get('shelves_code'):
            return Transaction().context['shelves_code']
        else:
            return None

    def get_quantity(self, name):
        pool = Pool()
        Uom = Pool().get('product.uom')
        Date = pool.get('ir.date')
        Location = Pool().get('stock.location')
        Product = pool.get('product.product')
        AvailableMedicineLine = pool.get("hrp_inventory.available_medicine_line")
        with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
            pbl = Product.products_by_location(
                [Transaction().context['location'], Location(Transaction().context['location']).freeze_location.id],
                with_childs=True)
        if name == 'quantity':
            if Transaction().context.get('shelves_code'):
                lines = AvailableMedicineLine.search([('product', '=', self.id),
                                                      ('warehouse', '=', Transaction().context['location'])])
                quantity = Uom.compute_qty(Product(self.id).template.default_uom.id,
                                           pbl[(Transaction().context['location'], self.id)],
                                           lines[0].scattered_uom.id)
                return quantity.quantize(decimal.Decimal('0.00'))
            number = pbl[(Transaction().context['location'], self.id)]
            return number
        if name == 'freeze_quantity':
            if Transaction().context.get('shelves_code'):
                lines = AvailableMedicineLine.search([('product', '=', self.id),
                                                      ('warehouse', '=', Transaction().context['location'])])
                freeze_quantity = Uom.compute_qty(Product(self.id).template.default_uom.id,
                                                  pbl[(
                                                      Location(Transaction().context['location']).freeze_location.id,
                                                      self.id)],
                                                  lines[0].scattered_uom.id)
                return freeze_quantity.quantize(decimal.Decimal('0.00'))
            number = pbl[(Location(Transaction().context['location']).freeze_location.id, self.id)]
            return number


class StockInventoryReportStart(ModelView):
    """StockInventoryReportStart"""
    __name__ = 'hrp_inventrory_report.stock_inventory_report_start'

    location = fields.Many2One('stock.location', 'location', select=True, required=True,
                               domain=[('type', '=', 'warehouse')],
                               states={'readonly': Bool(Eval('inventor_time'))}, depends=['inventor_time'])  # 库存地
    category = fields.Many2One('product.category', 'Category', select=True, required=True)  # 药品类型
    shelves_code = fields.Many2One('hrp_inventory.shelves_code', 'shelves_code', select=True)


class StockInventoryReportWizard(Wizard):
    """StockInventoryReportWizard"""
    __name__ = 'hrp_inventory_report.stock_inventory_report'

    start = StateView('hrp_inventrory_report.stock_inventory_report_start',
                      'hrp_inventory_report.hrp_inventory_report_stock_start_view_form', [
                          Button(u'取消', 'end', 'tryton-cancel'),
                          Button(u'打开', 'report', 'tryton-ok', default=True),
                      ])
    report = StateAction('hrp_inventory_report.act_hrp_inventory_report_stock')

    def do_report(self, action):
        context = {'location': self.start.location.id,
                   'category': self.start.category.id}
        if self.start.shelves_code:
            context['shelves_code'] = self.start.shelves_code.id
        action['pyson_context'] = PYSONEncoder().encode(context)
        action['name'] += ' - (%s) @ %s' % (self.start.location.name, self.start.category.name)
        return action, {}


# 药品出入库统计表

class StockShipmentOrderReport(ModelSQL, ModelView):
    """StockShipmentOrderReport"""
    __name__ = "hrp_inventory_report.stock_shipment_order_report"

    number = fields.Function(fields.Char('number', select=True), 'get_data')  # 序号
    party = fields.Many2One('party.party', 'party', select=True)  # 特定供应商
    name = fields.Function(fields.Char('name', select=True), 'get_data')  # 药批名称
    code = fields.Function(fields.Char('code', select=True), 'get_data')  # 编码
    category = fields.Function(fields.Char('category', select=True), 'get_data')  # 药品类型
    actual_payment = fields.Function(fields.Numeric('actual_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 实付金额
    wholesale_payment = fields.Function(fields.Numeric('wholesale_payment ', digits=(16, 2), readonly=True),
                                        'get_quantity')  # 批发金额
    retail_payment = fields.Function(fields.Numeric('retail_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 零售金额

    @staticmethod
    def table_query():
        pass

    def get_data(self, name):
        pass

    def get_quantity(self, name):
        pass


class StockShipmentCategoryReport(ModelSQL, ModelView):
    """StockShipmentCategoryReport"""
    __name__ = "hrp_inventory_report.stock_shipment_category_report"

    number = fields.Function(fields.Char('number', select=True), 'get_data')  # 序号
    party = fields.Many2One('party.party', 'party', select=True)  # 特定供应商
    name = fields.Function(fields.Char('name', select=True), 'get_data')  # 药批名次
    code = fields.Function(fields.Char('code', select=True), 'get_data')  # 编码
    category = fields.Function(fields.Char('category', select=True), 'get_data')  # 药品类型
    actual_payment = fields.Function(fields.Numeric('actual_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 实付金额
    wholesale_payment = fields.Function(fields.Numeric('wholesale_payment ', digits=(16, 2), readonly=True),
                                        'get_quantity')  # 批发金额
    retail_payment = fields.Function(fields.Numeric('retail_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 零售金额

    @staticmethod
    def table_query():
        pass

    def get_data(self, name):
        pass

    def get_quantity(self, name):
        pass


class StockShipmentOrderInReport(ModelSQL, ModelView):
    """StockShipmentOrderInReport"""
    __name__ = "hrp_inventory_report.stock_shipment_order_in_report"

    number = fields.Function(fields.Char('number', select=True), 'get_data')  # 序号
    party = fields.Many2One('party.party', 'party', select=True)  # 特定供应商
    order = fields.Char('order', select=True)  # 入库单号
    time_end = fields.Date('time_end', select=True, required=True)
    actual_payment = fields.Function(fields.Numeric('actual_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 实付金额
    wholesale_payment = fields.Function(fields.Numeric('wholesale_payment ', digits=(16, 2), readonly=True),
                                        'get_quantity')  # 批发金额
    retail_payment = fields.Function(fields.Numeric('retail_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 零售金额

    @staticmethod
    def table_query():
        pass

    def get_data(self, name):
        pass

    def get_quantity(self, name):
        pass


class StockShipmentInvoiceReport(ModelSQL, ModelView):
    """StockShipmentInvoiceReport"""
    __name__ = "hrp_inventory_report.stock_shipment_invoice_report"

    number = fields.Function(fields.Char('number', select=True), 'get_data')  # 序号
    party = fields.Many2One('party.party', 'party', select=True)  # 特定供应商
    order = fields.Char('order', select=True)  # 入库单号
    actual_payment = fields.Function(fields.Numeric('actual_payment', digits=(16, 2), readonly=True),
                                     'get_quantity')  # 实付金额
    invoice_number = fields.Function(fields.Char('invoice_number', select=True), 'get_invoice_number')

    @staticmethod
    def table_query():
        pass

    def get_data(self, name):
        pass

    def get_quantity(self, name):
        pass

    def get_invoice_number(self, name):
        pass


class StockShipmentReportStart(ModelView):
    """StockShipmentReportStart"""
    __name__ = 'hrp_inventory_report.stock_shipment_report_start'

    time_start = fields.Date('time_start', select=True, required=True)
    time_end = fields.Date('time_end', select=True, required=True)
    type = fields.Selection([  # 查询类型
        ('01', u'按药批的药品类型统计'),
        ('02', u'按结算票号统计'),
        ('03', u'按药批入库单号统计')
    ], 'Type', select=True, required=True)
    party = fields.Many2One('party.party', 'party', select=True)  # 特定供应商


class StockShipmentReportWizard(Wizard):
    """StockShipmentReportWizard"""
    __name__ = 'hrp_inventory_report.stock_shipment_report_wizard'

    start = StateView('hrp_inventory_report.stock_shipment_report_start',
                      'hrp_inventory_report.hrp_inventory_report_stock_shipment_report_start_view_form', [
                          Button(u'取消', 'end', 'tryton-cancel'),
                          Button(u'打开', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateTransition()
    category_report = StateAction('hrp_inventory_report.act_hrp_inventory_report_stock_shipment')
    order_report = StateAction('hrp_inventory_report.act_hrp_inventory_report_stock_shipment_order')
    invoice_report = StateAction('hrp_inventory_report.act_hrp_inventory_report_stock_shipment_invoice')

    def transition_create_(self):
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        if data['start']['type'] == '01':
            return 'category_report'
        elif data['start']['type'] == '03':
            return 'order_report'
        else:
            return 'invoice_report'

    def do_report(self, action):
        # context = {'location': self.start.location.id,
        #            'category': self.start.category.id}
        # if self.start.shelves_code:
        #     context['shelves_code'] = self.start.shelves_code.id
        # action['pyson_context'] = PYSONEncoder().encode(context)
        # action['name'] += ' - (%s) @ %s' % (self.start.location.name, self.start.category.name)
        return action, {}
