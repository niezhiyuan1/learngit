# coding:utf-8

import sys
import time
import operator
import decimal
from decimal import *
from trytond.report import Report
from trytond.model import ModelView, fields, ModelSQL
from trytond.pyson import If, Equal, Eval, Not, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, Button, StateReport
from trytond.pool import Pool, PoolMeta

reload(sys)
sys.setdefaultencoding('utf8')
__all__ = ['HrpShipmentLines', 'HrpShipment', 'CreatePurchaseShipment', 'ZdrugSaleorder', 'PurchaseBills', 'ShipmentIn',
           'ShipmentOrder',
           'HrpShipmentReturnLines', 'HrpShipmentReturn', 'CreatePurchaseShipmentReturn', 'ShipmentOrderLines',
           'CreateShipmentOrder', 'HrpSaleLines', 'HrpSale', 'HrpCreateSale', 'HrpSaleReport']

STATES = {
    'readonly': False,
}


class ShipmentIn:
    """Supplier Shipment"""
    __metaclass__ = PoolMeta
    __name__ = 'stock.shipment.in'
    _rec_name = 'number'
    in_storage = fields.Char('in_storage', readonly=True)  # 之后删除
    return_shipment = fields.Many2One('order_no', 'Return Shipment', select=True, readonly=False)  # 采退单号
    cause = fields.Selection([
        ('24', u'病人退费'),
        ('23', u'工作失误'),
        ('22', u'规格变更'),
        ('21', u'一品多规'),
        ('20', u'药品名称变更'),
        ('19', u'欠药病人不退'),
        ('18', u'盈亏误差'),
        ('17', u'入库错误'),
        ('16', u'近期药品'),
        ('15', u'处理破损药'),
        ('14', u'取未取药'),
        ('13', u'药剂科结余'),
        ('12', u'调批号'),
        ('11', u'科室换药'),
        ('10', u'原装破损'),
        ('09', u'科室基数'),
        ('08', u'损药换新'),
        ('07', u'新配制剂'),
        ('06', u'药品分装'),
        ('05', u'原料药消耗'),
        ('04', u'疫苗入库'),
        ('03', u'疫苗记帐'),
        ('02', u'疫苗支票'),
        ('01', u'退药'),
        ('00', u'正常'),
    ], 'cause')


# 采购入库
class PurchaseBills(ModelView, ModelSQL):
    """Purchase Bills"""
    __name__ = "purchase_bills"
    party = fields.Many2One('party.party', 'Party', states=STATES, readonly=True, select=False, )
    purchase_create_time = fields.Date('purchase_create_time', select=True)
    internal_order = fields.Integer('internal_order')
    internal_orders = fields.Char('internal_orders')
    order_code = fields.Char('order_code', readonly=True, select=True)
    line_code = fields.Integer('line_code')
    return_shipment = fields.Many2One('order_no', 'Return Shipment', select=True, readonly=True)
    product = fields.Many2One('product.product', 'Product', select=True)
    categories = fields.Many2One('product.category', 'Categories', select=True)
    purchase_quantity = fields.Integer('Purchase Quantity')
    shipment_quantity = fields.Integer('Shipment Quantity')
    invoice_code = fields.Char('invoice Code', )
    invoice_date = fields.Date('Invoice Date', )
    invoice_amount = fields.Numeric('Invoice Amount', digits=(16, 4), )
    amount_of_real_pay = fields.Numeric('amount_of_real_pay', digits=(16, 4), )
    retail_amount = fields.Float('retail_amount', digits=(16, 4), )
    lot = fields.Many2One('stock.lot', 'Lot', states=STATES, domain=[('product', '=', Eval('product')), ], )
    served_to = fields.Many2One('stock.location', 'served_to', required=True, )
    check = fields.Boolean('Check')
    message = fields.Char('message')
    state = fields.Selection([('draft', u'起草'), ('done', u'完成'), ('assigned', u'等待')], 'state')
    source = fields.Selection([
        ('00', u'采购'),
        ('01', u'手工'),
        ('02', u'扫码'),
        ('03', u'HIEP')], 'source')


class ZdrugSaleorder(ModelView, ModelSQL):
    "Zdrug Saleorder"
    __name__ = "hrp_shipment_zdrug_aleorder"

    line_code_system = fields.Integer('line_code_system')
    line_code = fields.Integer('Line Code')
    purchase_code = fields.Char('purchase_code')
    purchase_code_system = fields.Char('purchase_code')
    item_code = fields.Integer('Item Code', states=STATES)
    item_code_system = fields.Integer('item_code_system', states=STATES)
    drug_name = fields.Many2One('product.product', 'Drug Name')
    drug_specifications = fields.Char('drug_specifications')
    drug_specifications_system = fields.Char('drug_specifications_system')
    cost_price_system = fields.Numeric('cost_price_system', digits=(16, 4))
    cost_price = fields.Numeric('Cost Price', digits=(16, 4))
    list_price_system = fields.Numeric('list_price_system', digits=(16, 4))
    list_price = fields.Numeric('list_price', digits=(16, 4))
    retail_package = fields.Many2One('product.uom', 'Retail Package')
    retail_package_system = fields.Many2One('product.uom', 'Retail Package System')
    quantity = fields.Integer('Quantity')
    quantity_system = fields.Integer('quantity_system')
    invoice_amount = fields.Numeric('Invoice Amount', digits=(16, 4))
    retail_amount = fields.Float('retail_amount', digits=(16, 4))
    lot = fields.Many2One('stock.lot', 'Lot')
    dom = fields.Date('DOM')
    exp_date = fields.Date('exp_date')
    manufacturers_describtion_code = fields.Char('manufacturers_describtion_code')
    manufacturers_describtion = fields.Char('manufacturers_describtion')
    manufacturers_describtion_system = fields.Char('manufacturers_describtion_system')
    drug_approval_number = fields.Char('drug_approval_number')
    supply_name_code = fields.Char('supply_name_code')
    supply_name = fields.Many2One('party.party', 'supply_name')
    supply_name_system = fields.Many2One('party.party', 'supply_name')
    invoice_date = fields.Date('invoice_date')
    invoice_code = fields.Char('invoice Code')
    purchaser_coding = fields.Char('purchaser_coding')
    original_sales_order = fields.Char('original_sales_order')
    original_sales_lines = fields.Char('original_sales_lines')
    sales_date = fields.Date('sales_date')
    sellers_text = fields.Char('sellers_text')
    purchaser_text = fields.Char('purchaser_text')
    material_no = fields.Char('material_no')
    dosage_form = fields.Char('dosage_form')
    smallest_unit_of = fields.Char('smallest_unit_of')
    manufacturer_number = fields.Char('manufacturer_number')
    number_of_units = fields.Char('number_of_units')
    wholesale_price = fields.Char('wholesale_price')
    packing_unit = fields.Char('Packing unit')
    original_purchase_order_no = fields.Char('original_purchase_order_no')
    original_purchase_number_line = fields.Char('original_purchase_number_line')
    bar_code_number = fields.Char('bar_code_number')
    deal_with_logo = fields.Char('deal_with_logo')
    note = fields.Char('Note')
    arriving = fields.Many2One('stock.location', 'Arring')
    drug_code = fields.Char('Drug Code')
    state = fields.Boolean('State')
    is_electronic_invoice = fields.Boolean('is_electronic_invoice')
    in_storage = fields.Char('in_storage')


class HrpShipmentLines(ModelView):
    "Hrp_shipment_lines"
    __name__ = "hrp_shipment_lines"
    _rec_name = 'HrpShipmentLines'

    purchase_bills = fields.Many2One('purchase_bills', 'purchase_bills')
    name = fields.Function(fields.Char('name', readonly=True), 'get_name')
    is_electronic_invoice = fields.Boolean('is_electronic_invoice', readonly=True)
    number = fields.Char('number', readonly=True)
    line_code = fields.Integer('Line Code', states=STATES)
    state = fields.Boolean('State', states=STATES)
    supply_name = fields.Many2One('party.party', 'Supply Name',
                                  domain=[('type_', '=', 'supply')], states=STATES)
    purchase_code = fields.Char('Puechase Code', states=STATES)
    item_code = fields.Integer('Item Code', states=STATES)
    drug_code = fields.Char('Drug Code', states=STATES, readonly=True)
    drug_specifications = fields.Char('Drug Speic', states=STATES, readonly=True)
    purchase_create_time = fields.Date('purchase_create_time', select=True)
    manufacturers_describtion = fields.Char('Manufacturers Describtion', states=STATES, readonly=True)
    quantity = fields.Integer('Quantity', states=STATES)
    retail_package = fields.Many2One('product.uom', 'Retail Package', states=STATES, readonly=True)
    list_price = fields.Numeric('List Price', digits=(16, 4), states=STATES, readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), states=STATES, readonly=True)
    invoice_code = fields.Char('invoice Code', states=STATES)
    invoice_date = fields.Date('Invoice Date', states=STATES)
    invoice_amount = fields.Numeric('Invoice Amount', digits=(16, 4), states=STATES)
    drug_approval_number = fields.Char('Drug Approval Number', states=STATES)
    product = fields.Many2One('product.product', 'Product')
    lot = fields.Many2One('stock.lot', 'Lot', states=STATES, domain=[
        ('product', '=', Eval('product')),
    ], depends=['product'])
    dom = fields.Function(fields.Date('DOM', states=STATES, readonly=True), 'get_dom', 'set_dom')
    exp_date = fields.Function(fields.Date('Exp Date', states=STATES, readonly=True), 'get_exp_date', 'set_exp_date')
    arriving = fields.Many2One('stock.location', 'Arring', states=STATES)
    retail_amount = fields.Numeric('retail_amount', digits=(16, 4), states=STATES)
    error_message = fields.Char('Error Message', required=True, readonly=True)

    def get_name(self, name):
        return self.product.template.name

    @fields.depends('state', 'list_price', 'cost_price', 'retail_amount', 'invoice_amount', 'product',
                    'manufacturers_describtion', 'quantity',
                    'drug_approval_number', 'error_message', 'lot', 'invoice_code', 'invoice_date')
    def on_change_state(self, name=None):
        Date = Pool().get('ir.date')
        today = Date.today()
        if self.state == True:
            if not self.invoice_amount or not self.retail_amount or not self.lot or not self.invoice_code or not self.invoice_date:
                self.state = False
                self.error_message = u'请填写完整信息'
            elif self.lot.shelf_life_expiration_date < today:
                pass
                # self.state = False
                # self.error_message = u'所选批次已超过有效期'
            elif self.product.template.is_atict == True and round(
                            self.cost_price * decimal.Decimal(str(self.quantity))) < round(self.invoice_amount):
                self.state = False
                self.error_message = u'校验超出容差范围'
            elif round(self.list_price * decimal.Decimal(str(self.quantity))) != round(self.retail_amount):
                self.state = False
                self.error_message = u'校验零售金额不符'
            elif self.product.template.manufacturers_describtion != self.manufacturers_describtion:
                self.state = False
                self.error_message = u'校验厂商不符'
            elif self.product.template.approval_number != self.drug_approval_number:
                self.state = False
                self.error_message = u'校验批准文号不符'
            elif self.product.template.is_atict == False and round(
                            self.cost_price * decimal.Decimal(str(self.quantity))) != round(self.invoice_amount):
                self.state = False
                self.error_message = u'校验发票金额不符'
            else:
                self.state = True
                self.error_message = u''

    @fields.depends('quantity', 'list_price', 'invoice_amount', 'cost_price')
    def on_change_quantity(self, name=None):
        if self.quantity:
            self.retail_amount = decimal.Decimal(str(self.quantity)) * self.list_price
            self.invoice_amount = decimal.Decimal(str(self.quantity)) * self.cost_price

    @fields.depends('lot', 'dom', 'exp_date', 'error_message')
    def on_change_lot(self, name=None):
        if self.lot:
            Date = Pool().get('ir.date')
            today = Date.today()
            if today > self.lot.shelf_life_expiration_date:
                self.error_message = u'所选批次已超过有效期'
            else:
                self.dom = self.lot.date_of_production
                self.exp_date = self.lot.shelf_life_expiration_date

    def get_dom(self, name):
        if self.lot:
            return self.lot.date_of_production

    def get_exp_date(self, name):
        if self.lot:
            Date = Pool().get('ir.date')
            today = Date.today()
            if today > self.lot.shelf_life_expiration_date:
                self.raise_user_error(u'所选批次已超过有效期')
            return self.lot.shelf_life_expiration_date

    @classmethod
    def set_dom(cls, set_name, name, value):
        pass

    @classmethod
    def set_exp_date(cls, set_exp_date, name, value):
        pass


class HrpShipment(ModelView):
    "Hrp_shipment"
    __name__ = "hrp_shipment"
    supply_name = fields.Many2One('party.party', 'Supply Name',
                                  domain=[
                                      ('type_', '=', 'supplier')
                                  ])
    retrieve_the_code = fields.Many2One('product.product', 'Retrieve The Code', help='Drugs in code')
    purchase_code = fields.Char('Purchase Code')
    into_code = fields.Char('Into Code')
    hrp_shipment_lines = fields.One2Many('hrp_shipment_lines', '', 'Hrp Shipment Lines')
    incoming_information = fields.Boolean('Incoming Information')
    electronic_invoice = fields.Boolean('Electronic Invoice')

    @fields.depends('retrieve_the_code', 'hrp_shipment_lines', 'electronic_invoice')
    def on_change_retrieve_the_code(self, name=None):
        PurchaseBills = Pool().get('purchase_bills')
        if self.electronic_invoice:
            search = [('state', '=', 'done'), ('source', '!=', '00')]
            if self.supply_name:
                party_id = ('party', '=', self.supply_name)
                search.append(party_id)
            if self.retrieve_the_code:
                product_id = ('product', '=', self.retrieve_the_code)
                search.append(product_id)
            if self.purchase_code:
                purchase_id = ('number', '=', self.purchase_code)
                search.append(purchase_id)
                #####需要去hiep 去抓取电子发票信息然后保存在本地
            purchase_details = PurchaseBills.search(search)  # 根据条件去系统搜索内容
            list = []
            if purchase_details:
                for details in purchase_details:
                    dict = {}
                    dict['purchase_bills'] = details.id
                    dict['purchase_create_time'] = details.purchase_create_time
                    dict['line_code'] = details.line_code
                    dict['supply_name'] = details.party.id
                    dict['purchase_code'] = details.order_code
                    dict['arriving'] = details.served_to.id
                    dict['item_code'] = details.line_code
                    dict['drug_code'] = details.product_code
                    dict['drug_specifications'] = details.drug_specifications
                    dict['product'] = details.product.id
                    dict['manufacturers_describtion'] = details.manufacturers
                    dict['quantity'] = details.purchase_quantity
                    dict['retail_package'] = details.product.template.retail_package
                    dict['cost_price'] = details.product.template.cost_price
                    dict['name'] = details.product_name
                    dict['list_price'] = details.product.template.list_price
                    dict['retail_amount'] = details.retail_amount
                    dict['drug_approval_number'] = details.approval_number
                    dict['invoice_amount'] = details.invoice_amount
                    dict['retrieve_the_code'] = False
                    list.append(dict)
                list.sort(key=lambda x: x['purchase_create_time'], reverse=True)
            self.hrp_shipment_lines = list
        else:
            self.hrp_shipment_lines = []

    @fields.depends('supply_name', 'retrieve_the_code', 'purchase_code', 'drug_type', 'arriving', 'into_code',
                    'incoming_information')
    def on_change_incoming_information(self, name=None):
        pass

    @fields.depends('supply_name', 'retrieve_the_code', 'purchase_code', 'drug_type', 'arriving', 'electronic_invoice',
                    'hrp_shipment_lines')
    def on_change_electronic_invoice(self):
        """
        :param name:
        """
        PurchaseBills = Pool().get('purchase_bills')
        if self.electronic_invoice == True:
            search = [('state', '=', 'draft'), ('source', '=', '00')]
            if self.supply_name:
                party_id = ('party', '=', self.supply_name)
                search.append(party_id)
            if self.retrieve_the_code:
                product_id = ('product', '=', self.retrieve_the_code)
                search.append(product_id)
            if self.purchase_code:
                purchase_id = ('order_code', '=', self.purchase_code)
                search.append(purchase_id)
                #####需要去hiep 去抓取电子发票信息然后保存在本地
            purchase_details = PurchaseBills.search(search)  # 根据条件去系统搜索内容
            list = []
            if purchase_details:
                for details in purchase_details:
                    dict = {}
                    dict['purchase_bills'] = details.id
                    dict['purchase_create_time'] = details.purchase_create_time
                    dict['line_code'] = details.line_code
                    dict['supply_name'] = details.party.id
                    dict['purchase_code'] = details.order_code
                    dict['arriving'] = details.served_to.id
                    dict['item_code'] = details.line_code
                    dict['drug_code'] = details.product.code
                    dict['drug_specifications'] = details.product.template.drug_specifications
                    dict['product'] = details.product.id
                    dict['manufacturers_describtion'] = details.product.template.manufacturers_describtion
                    dict['quantity'] = details.purchase_quantity
                    dict['retail_package'] = details.product.template.retail_package
                    dict['cost_price'] = details.product.template.cost_price
                    dict['name'] = details.product.name
                    dict['list_price'] = details.product.template.list_price
                    dict['retail_amount'] = details.product.template.list_price * decimal.Decimal(
                        str(details.purchase_quantity))
                    dict['drug_approval_number'] = details.product.template.approval_number
                    dict['invoice_amount'] = details.product.template.cost_price * decimal.Decimal(
                        str(details.purchase_quantity))
                    dict['is_electronic_invoice'] = False
                    list.append(dict)
                list.sort(key=lambda x: x['purchase_code'], reverse=True)
            self.hrp_shipment_lines = list
        else:
            self.hrp_shipment_lines = []


class CreatePurchaseShipment(Wizard):
    'Create Purchase Shipment'
    __name__ = 'create_purchase_shipment'
    start = StateView('hrp_shipment',
                      'hrp_shipment.hrp_shipment_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_hrp_shipment_create')

    def do_create_(self, action):
        Line = Pool().get('purchase.line')
        OrderNo = Pool().get('order_no')
        PurchaseBills = Pool().get('purchase_bills')
        Sequence = Pool().get('ir.sequence')
        Internal = Pool().get('stock.shipment.internal')
        Invoice = Pool().get('account.invoice')
        ShipmentIn = Pool().get('stock.shipment.in')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        Date = Pool().get('ir.date')
        Move = Pool().get('stock.move')
        today = str(Date.today())
        data = {}
        InternalIn_list = []
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        Purchase = Pool().get('purchase.purchase')
        if data != {}:
            nnum = 0
            shipment_purchase_order = OrderNo.search([('order_category', '=', 'return')],
                                                     order=[["create_date", "DESC"]])

            if shipment_purchase_order and int(shipment_purchase_order[0].number[:6]) == int(
                    time.strftime('%Y%m', time.localtime())):
                squence = time.strftime('%Y%m', time.localtime()) + str(
                    int(shipment_purchase_order[0].number[7:]) + 1).zfill(4)
            else:
                squence = time.strftime('%Y%m', time.localtime()) + '1'.zfill(4)
            return_shipment = OrderNo.create([{'number': squence, 'time': today, 'order_category': 'return'}])
            for hrp_shipment_lines in data['start']['hrp_shipment_lines']:
                purchase_bills = PurchaseBills.search([('id', '=', hrp_shipment_lines['purchase_bills'])])
                purchase = Purchase.search([('number', '=', hrp_shipment_lines['purchase_code'])])
                pruchase_line = Line.search([('sequence', '=', hrp_shipment_lines['line_code']),
                                             ('purchase', '=', purchase[0].id)])

                if pruchase_line[0].unit_price != hrp_shipment_lines['cost_price']:
                    Purchase.draft(purchase)
                    Line.write(pruchase_line, {'unit_price': hrp_shipment_lines['cost_price']})
                    Purchase.quote(purchase)
                dict_purchase_bills = {}
                dict_purchase_bills['lot'] = hrp_shipment_lines['lot']
                dict_purchase_bills['shipment_quantity'] = hrp_shipment_lines['quantity']
                dict_purchase_bills['invoice_code'] = hrp_shipment_lines['invoice_code']
                dict_purchase_bills['invoice_date'] = hrp_shipment_lines['invoice_date']
                dict_purchase_bills['check'] = hrp_shipment_lines['state']
                dict_purchase_bills['state'] = 'assigned'
                dict_purchase_bills['source'] = '01'
                dict_purchase_bills['amount_of_real_pay'] = hrp_shipment_lines['invoice_amount']
                dict_purchase_bills['lot'] = hrp_shipment_lines['lot']
                dict_purchase_bills['return_shipment'] = return_shipment[0].id
                if hrp_shipment_lines['state'] == True and hrp_shipment_lines['arriving'] == config.warehouse.id:
                    if purchase_bills[0].purchase_quantity == hrp_shipment_lines['quantity']:
                        PurchaseBills.write(purchase_bills, dict_purchase_bills)
                    elif hrp_shipment_lines['quantity'] < purchase_bills[0].purchase_quantity:
                        PurchaseBills.write(purchase_bills, dict_purchase_bills)
                        dict_purchase = {}
                        dict_purchase['party'] = purchase_bills[0].party
                        dict_purchase['purchase_create_time'] = purchase_bills[0].purchase_create_time
                        dict_purchase['order_code'] = purchase_bills[0].order_code
                        dict_purchase['served_to'] = purchase_bills[0].served_to
                        dict_purchase['state'] = 'draft'
                        dict_purchase['source'] = '00'
                        dict_purchase['line_code'] = purchase_bills[0].line_code
                        dict_purchase['product'] = purchase_bills[0].product
                        dict_purchase['categories'] = purchase_bills[0].categories
                        dict_purchase['purchase_quantity'] = purchase_bills[0].purchase_quantity - hrp_shipment_lines[
                            'quantity']
                        dict_purchase['amount_of_real_pay'] = hrp_shipment_lines['invoice_amount']
                        dict_purchase['invoice_amount'] = hrp_shipment_lines['cost_price'] * decimal.Decimal(
                            str(purchase_bills[0].purchase_quantity - hrp_shipment_lines['quantity']))
                        dict_purchase['retail_amount'] = round(hrp_shipment_lines['list_price'] * decimal.Decimal(
                            str(purchase_bills[0].purchase_quantity - hrp_shipment_lines['quantity'])))
                        PurchaseBills.create([dict_purchase])
                    else:
                        self.raise_user_error(u'数量大于%s' % purchase_bills[0].purchase_quantity)
                if hrp_shipment_lines['state'] == True and hrp_shipment_lines['arriving'] != config.warehouse.id:
                    if purchase_bills[0].purchase_quantity == hrp_shipment_lines['quantity']:
                        dict_purchase_bills['state'] = 'done'
                        PurchaseBills.write(purchase_bills, dict_purchase_bills)
                    elif purchase_bills[0].purchase_quantity > hrp_shipment_lines['quantity']:
                        PurchaseBills.write(purchase_bills, dict_purchase_bills)
                        dict_purchase = {}
                        dict_purchase['party'] = purchase_bills[0].party
                        dict_purchase['purchase_create_time'] = purchase_bills[0].purchase_create_time
                        dict_purchase['order_code'] = purchase_bills[0].order_code
                        dict_purchase['served_to'] = purchase_bills[0].served_to
                        dict_purchase['state'] = 'done'
                        dict_purchase['source'] = '00'
                        dict_purchase['line_code'] = purchase_bills[0].line_code
                        dict_purchase['product'] = purchase_bills[0].product
                        dict_purchase['categories'] = purchase_bills[0].categories
                        internal_orders = str(purchase_bills[0].internal_orders)
                        dict_purchase['internal_orders'] = internal_orders
                        dict_purchase['purchase_quantity'] = purchase_bills[0].purchase_quantity - hrp_shipment_lines[
                            'quantity']
                        dict_purchase['amount_of_real_pay'] = hrp_shipment_lines['invoice_amount']
                        dict_purchase['invoice_amount'] = hrp_shipment_lines['cost_price'] * decimal.Decimal(
                            str(purchase_bills[0].purchase_quantity - hrp_shipment_lines['quantity']))
                        dict_purchase['retail_amount'] = round(hrp_shipment_lines['list_price'] * decimal.Decimal(
                            str(purchase_bills[0].purchase_quantity - hrp_shipment_lines['quantity'])))
                        PurchaseBills.create([dict_purchase])
                    else:
                        self.raise_user_error(u'数量大于%s' % purchase_bills[0].purchase_quantity)
                    Purchase.quote(purchase)
                    Purchase.confirm(purchase)
                    Purchase.process(purchase)
                    moves = Move.search([
                        ('product', '=', hrp_shipment_lines['product']),
                        ('purchase', '=', hrp_shipment_lines['purchase_code']),
                        ('state', '=', 'draft')
                    ])
                    Move.write(moves, {'outgoing_audit': '02', 'lot': hrp_shipment_lines['lot'],
                                       'quantity': hrp_shipment_lines['quantity'], 'move_type': '101'})
                    lv = {}
                    if moves != []:
                        lv['incoming_moves'] = [['add', [moves[0].id]]]
                    lv['reference'] = ''
                    lv['planned_date'] = today
                    lv['return_shipment'] = return_shipment[0].id
                    lv['company'] = Transaction().context.get('company')
                    lv['effective_date'] = None
                    lv['warehouse'] = config.warehouse.id
                    lv['cause'] = '00'
                    lv['supplier'] = hrp_shipment_lines['supply_name']
                    lv['inventory_moves'] = []
                    shipments = ShipmentIn.create([lv])
                    shipment = ShipmentIn.search([('id', '=', shipments[0].id)])
                    ShipmentIn.receive(shipment)
                    ShipmentIn.done(shipment)
                    invoices = Invoice.search([
                        ('state', '=', 'draft'),
                        ('id', 'in', [ids.id for ids in [i for i in [k.invoices for k in purchase]][0]])
                    ])
                    Invoice.write(invoices, {'invoice_date': hrp_shipment_lines['invoice_date'],
                                             'reference': hrp_shipment_lines['invoice_code'],
                                             'description': return_shipment[0].number,
                                             'amount': hrp_shipment_lines['invoice_amount']})
                    nnum += 1
                    Invoice.validate_invoice(invoices)
                    Invoice.validate_invoice(invoices)
                    InternalIn = Internal.search([
                        ('number', '=', str(purchase_bills[0].internal_orders)),
                        ('place_of_service', '=', purchase_bills[0].served_to.id),
                        ('state', '=', 'draft')
                    ])
                    # try:
                    if True:
                        InternalIn_list.append(InternalIn)
                        Internal_move = Move.search([(
                            ('shipment', '=', 'stock.shipment.internal,' + str(InternalIn[0].id)),
                            ('state', '=', 'draft')
                        )])
                        for Internal_move_line in Internal_move:
                            if Internal_move_line.product.id == hrp_shipment_lines[
                                'product'] and Internal_move_line.check_move == False and Internal_move_line.purchase_order == \
                                    hrp_shipment_lines['purchase_code']:
                                if Internal_move_line.quantity > hrp_shipment_lines['quantity'] and \
                                                hrp_shipment_lines['quantity'] < purchase_bills[0].purchase_quantity:
                                    Move.write([Internal_move_line],
                                               {'quantity': hrp_shipment_lines['quantity'], 'check_move': True,
                                                'outgoing_audit': '00'})
                                    dict = {}
                                    dict['origin'] = None  # each['origin']
                                    dict['to_location'] = config.transfers.id  # 中转库
                                    dict['product'] = hrp_shipment_lines['product']
                                    dict['from_location'] = Internal_move_line.from_location.id
                                    dict['invoice_lines'] = ()  # each['invoice_lines']
                                    dict['company'] = Transaction().context.get('company')
                                    dict['is_direct_sending'] = True  # 是否直送
                                    dict['unit_price'] = Internal_move_line.product.template.list_price  # 产品的价格
                                    dict['lot'] = None
                                    dict['purchase_order'] = hrp_shipment_lines['purchase_code']
                                    dict['change_start'] = False
                                    dict['outgoing_audit'] = '03'
                                    dict['starts'] = '06'
                                    dict['uom'] = Internal_move_line.product.template.default_uom
                                    dict['real_number'] = Internal_move_line.real_number  # 产品的请领数量
                                    dict['quantity'] = (
                                        purchase_bills[0].purchase_quantity - hrp_shipment_lines['quantity'])
                                    dict['shipment'] = 'stock.shipment.internal,' + str(InternalIn[0].id)
                                    Move.create([dict])
                                if hrp_shipment_lines['quantity'] == purchase_bills[0].purchase_quantity:
                                    Move.write([Internal_move_line],
                                               {'quantity': hrp_shipment_lines['quantity'], 'check_move': True,
                                                'outgoing_audit': '00'})
                                if hrp_shipment_lines['quantity'] > purchase_bills[0].purchase_quantity:
                                    self.raise_user_error(u'数量大于%s' % purchase_bills[0].purchase_quantity)
                            if Internal_move_line.product.id != hrp_shipment_lines[
                                'product'] and Internal_move_line.check_move == False:
                                Move.write([Internal_move_line], {'outgoing_audit': '03'})
                            if Internal_move_line.product.id == hrp_shipment_lines[
                                'product'] and Internal_move_line.check_move == False and Internal_move_line.purchase_order != \
                                    hrp_shipment_lines['purchase_code']:
                                Move.write([Internal_move_line], {'outgoing_audit': '03'})
                                # except:
                                #     self.raise_user_error(u'此采购单所对应的请领单无效')

            if InternalIn_list != []:
                for i in InternalIn_list:
                    Internal.wait(i)
                    Internal.assign(i)
                    Internal.done(i)
        return action, {}


# 采购退货
class HrpShipmentReturnLines(ModelView):
    "HrpShipmentReturnLines"
    __name__ = "hrp_shipment_return_lines"
    _rec_name = 'HrpShipmentReturnLines'

    invoice_date = fields.Date('invoice_date')
    invoice_code = fields.Char('invoice Code')
    cost_price = fields.Numeric('Cost Price', digits=(16, 4))
    supply_name = fields.Many2One('party.party', 'Supply Name',
                                  domain=[
                                      ('type_', '=', 'supplier')
                                  ])
    code = fields.Char('code', readonly=True)
    product = fields.Many2One('product.product', 'Product', readonly=True)
    product_name = fields.Char('Product_name', readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    retail_package = fields.Many2One('product.uom', 'Retail Package', readonly=True)
    invoice_amount = fields.Numeric('Invoice Amount', digits=(16, 4), readonly=True)
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
        ('product', '=', Eval('product')),
    ], readonly=True)
    drug_approval_number = fields.Char('Drug Approval Number', readonly=True)
    manufacturers_describtion = fields.Char('Manufacturers_describtion', readonly=True)
    note = fields.Char('Note', readonly=True)


class HrpShipmentReturn(ModelView):
    "HrpShipmentReturn"
    __name__ = "hrp_shipment_return"
    supply_name = fields.Many2One('party.party', 'Supply Name',
                                  domain=[
                                      ('type_', '=', 'supplier')
                                  ])
    product = fields.Function(
        fields.One2Many('product.product', None, 'Product', depends=['categories']),
        'on_change_with_product')
    categories = fields.Many2One('product.category', 'Categories', select=True, required=True, states={
        'readonly': Bool(Eval('shipment_return_lines'))})
    lots = fields.Function(
        fields.One2Many('stock.lot', None, 'Lots'),
        'on_change_with_lots')
    retrieve_the_code = fields.Many2One('product.product', 'Retrieve The Code', domain=[
        ('id', 'in', Eval('product')),
    ], depends=['product'], help='Drugs in code')
    drug_specifications = fields.Char('Drug_specifications', readonly=True)
    drug_approval_number = fields.Char('Drug Approval Number', readonly=True)
    manufacturers_describtion = fields.Char('Manufacturers_describtion', readonly=True)
    warehouse = fields.Many2One('stock.location', 'warehouse', readonly=False)
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    retail_package = fields.Many2One('product.uom', 'Retail Package', domain=[
        ('category', '=', Eval('product_uom_category')),
    ],
                                     depends=['product_uom_category'], )

    quantity = fields.Integer('Quantity')
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
        ('product', '=', Eval('retrieve_the_code')),
        ('id', 'in', Eval('lots')),
    ], context={
        'locations': [Eval('warehouse')],
    }, required=False, depends=['product', 'lots', 'warehouse'])
    list_price = fields.Numeric('List Price', digits=(16, 4))
    cost_price = fields.Numeric('Cost Price', digits=(16, 4))
    invoice_date = fields.Date('invoice_d ate')
    invoice_code = fields.Char('invoice Code')
    invoice_amount = fields.Numeric('Invoice Amount', digits=(16, 4))
    note = fields.Char('Note')
    shipment_return = fields.Boolean('Shipment Return')
    shipment_return_lines = fields.One2Many('hrp_shipment_return_lines', None, 'HrpShipmentReturnLines')

    @fields.depends('retrieve_the_code')
    def on_change_with_product_uom_category(self, name=None):
        if self.retrieve_the_code:
            return self.retrieve_the_code.default_uom_category.id

    @fields.depends('cost_price', 'quantity', 'invoice_amount')
    def on_change_cost_price(self, name=None):
        if not self.cost_price:
            self.invoice_amount = decimal.Decimal('0')
        else:
            self.invoice_amount = self.cost_price * decimal.Decimal(str(self.quantity))

    @fields.depends('quantity', 'lot')
    def on_change_lot(self, name=None):
        if self.lot:
            self.quantity = None

    @fields.depends('cost_price', 'quantity', 'invoice_amount', 'lot', 'warehouse', 'retrieve_the_code',
                    'shipment_return_lines', 'retail_package')
    def on_change_quantity(self, name=None):
        if self.lot and self.retail_package:
            if not self.quantity:
                self.invoice_amount = decimal.Decimal('0')
            else:
                Product = Pool().get('product.product')
                Date = Pool().get('ir.date')
                context = ({'stock_date_end': Date.today()})
                with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                    pbl = Product.products_by_location([self.warehouse.id], [self.retrieve_the_code.id],
                                                       with_childs=True, grouping=('product', 'lot'))
                    quantity = pbl[(self.warehouse.id, self.retrieve_the_code.id, self.lot.id)]
                factor = round((self.retrieve_the_code.default_uom.factor * self.retail_package.rate), 3)  # 单位换算
                quantity_all = self.quantity * factor
                quantity_line = 0
                for lines_quantity in self.shipment_return_lines:
                    factor_line = round(
                        (lines_quantity.product.default_uom.factor * lines_quantity.retail_package.rate), 3)  # 单位换算
                    if self.retrieve_the_code == lines_quantity.product:
                        quantity_all += lines_quantity.quantity * factor_line
                        quantity_line += lines_quantity.quantity * factor_line
                if quantity < quantity_all:
                    self.quantity = 0
                    self.raise_user_error(
                        u'数量应小于%s%s' % (quantity - quantity_line, self.retrieve_the_code.default_uom.name))
                else:
                    self.invoice_amount = self.cost_price * self.quantity
        else:
            self.quantity = 0
            self.raise_user_error(u'请填写批次')

    @fields.depends('retrieve_the_code')
    def on_change_retrieve_the_code(self, name=None):
        if self.retrieve_the_code:
            pool = Pool()
            try:
                product_templates = pool.get('product.template')
                product_template = product_templates.search([
                    ("id", "=", int(self.retrieve_the_code.template))
                ])
                manufacturers_describtion = product_template[0].manufacturers_describtion
                retail_package = product_template[0].default_uom.id
                drug_approval_number = product_template[0].approval_number
                drug_specifications = product_template[0].drug_specifications
                self.supply_name = product_template[0].product_suppliers[0].party.id
                self.list_price = product_template[0].list_price
                self.cost_price = -(product_template[0].cost_price)
                self.drug_specifications = drug_specifications
                self.drug_approval_number = drug_approval_number
                self.retail_package = retail_package
                self.manufacturers_describtion = manufacturers_describtion
                self.lot = None
            except:
                return None

    @fields.depends('warehouse', 'categories')
    def on_change_with_product(self, name=None):
        if self.warehouse and self.categories:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                ces = Product.products_by_location([self.warehouse.id], with_childs=True)
                lists = ces.keys()
                list_c = []
                for i in lists:
                    product = Product.search([('id', '=', i[1])])
                    if not product:
                        continue
                    categories = product[0].template.categories[0].id
                    if ces[i] <= 0.0 or categories != self.categories.id:
                        list_c.append(i)
                for g in list_c:
                    lists.remove(g)
                product_ids = []
                for g in lists:
                    product_ids.append(g[1])
            return product_ids

    @fields.depends('warehouse')
    def on_change_with_lots(self, name=None):
        if self.warehouse:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            Lot = Pool().get('stock.lot')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.warehouse], with_childs=True, grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value > 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('shipment_return', 'supply_name', 'retrieve_the_code', 'drug_specifications', 'cost_price',
                    'invoice_code',
                    'drug_approval_number', 'manufacturers_describtion', 'quantity', 'retail_package', 'invoice_amount',
                    'lot', 'note', 'invoice_date')
    def on_change_shipment_return(self, name=None):
        if self.shipment_return == True and self.supply_name != None and self.retrieve_the_code != None and self.lot != None \
                and self.retail_package != None and self.invoice_amount and self.quantity:
            list = []
            dict = {}
            dict['code'] = self.retrieve_the_code.code
            dict['product'] = self.retrieve_the_code.id
            dict['product_name'] = self.retrieve_the_code.name
            dict['drug_specifications'] = self.drug_specifications
            dict['quantity'] = self.quantity
            dict['retail_package'] = self.retail_package.id
            dict['invoice_amount'] = self.invoice_amount
            dict['lot'] = self.lot.id
            dict['supply_name'] = self.supply_name.id
            dict['cost_price'] = self.cost_price
            dict['drug_approval_number'] = self.drug_approval_number
            dict['manufacturers_describtion'] = self.manufacturers_describtion
            dict['invoice_code'] = self.invoice_code
            dict['invoice_date'] = self.invoice_date
            dict['note'] = self.note
            list.append(dict)
            self.shipment_return_lines = list
            self.retrieve_the_code = None
            self.supply_name = None
            self.shipment_return = None
            self.drug_specifications = None
            self.drug_approval_number = None
            self.manufacturers_describtion = None
            self.quantity = None
            self.retail_package = None
            self.invoice_amount = None
            self.invoice_code = None
            self.lot = None
            self.note = None
            self.cost_price = None
            self.list_price = None

    @staticmethod
    def default_warehouse():
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        if config.return_of.id:
            return config.return_of.id
        else:
            raise ValueError(u'请先创建采购配置')

    @staticmethod
    def default_invoice_date():
        Date_ = Pool().get('ir.date')
        return Date_.today()


class CreatePurchaseShipmentReturn(Wizard):
    'Create Purchase Shipment Return'
    __name__ = 'create_purchase_shipment_return'
    start = StateView('hrp_shipment_return',
                      'hrp_shipment.hrp_shipment_return_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_hrp_shipment_return_create')

    def do_create_(self, action):
        Party = Pool().get('party.party')
        Product = Pool().get('product.product')
        OrderNo = Pool().get('order_no')
        Sequence = Pool().get('ir.sequence')
        Invoice = Pool().get('account.invoice')
        ShipmentInReturn = Pool().get('stock.shipment.in.return')
        Config = Pool().get('purchase.configuration')
        Config1 = Pool().get('stock.configuration')
        config1 = Config1(1)
        config = Config(1)
        from_location = config.return_of.id
        Company = Pool().get('company.company')
        company = Company.search([('id', '=', Transaction().context['company'])])
        currency = company[0].currency
        Date = Pool().get('ir.date')
        Move = Pool().get('stock.move')
        Lot = Pool().get('stock.lot')
        today = str(Date.today())
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        shipment_in_return_order = OrderNo.search([('order_category', '=', 'return')], order=[["create_date", "DESC"]])

        if shipment_in_return_order and int(shipment_in_return_order[0].number[:6]) == int(
                time.strftime('%Y%m', time.localtime())):
            squence = time.strftime('%Y%m', time.localtime()) + str(
                int(shipment_in_return_order[0].number[7:]) + 1).zfill(4)
        else:
            squence = time.strftime('%Y%m', time.localtime()) + '1'.zfill(4)
        order_no = OrderNo.create([{'number': squence, 'time': today, 'order_category': 'return'}])
        if data != {}:
            message = ''
            for hrp_shipment_return_lines in data['start']['shipment_return_lines']:
                party = Party.search([('id', '=', hrp_shipment_return_lines['supply_name'])])
                product = Product.search([('id', '=', hrp_shipment_return_lines['product'])])
                invoice_dict = {}
                invoice_dict['comment'] = ''
                invoice_dict['account'] = 4
                invoice_dict['description'] = ''
                invoice_dict['reference'] = hrp_shipment_return_lines['invoice_code']
                invoice_dict['payment_term'] = party[0].supplier_payment_term.id
                invoice_dict['journal'] = 2
                invoice_dict['invoice_date'] = hrp_shipment_return_lines['invoice_date']
                invoice_dict['amount'] = hrp_shipment_return_lines['invoice_amount']
                invoice_dict['company'] = Transaction().context.get('company')
                invoice_dict['lines'] = [[
                    u'create',
                    [
                        {
                            u'stock_moves': [],
                            u'description': product[0].name,
                            u'sequence': 1,
                            u'invoice_type': None,
                            u'company': Transaction().context.get('company'),
                            u'product': hrp_shipment_return_lines['product'],
                            u'unit_price': hrp_shipment_return_lines['cost_price'],
                            u'note': hrp_shipment_return_lines['note'],
                            u'currency': currency.id,
                            u'taxes': [],
                            u'account': product[0].account_expense_used,
                            u'party': None,
                            u'type': u'line',
                            u'unit': hrp_shipment_return_lines['retail_package'],
                            u'quantity': hrp_shipment_return_lines['quantity']
                        }
                    ]
                ]]
                invoice_dict['taxes'] = []
                invoice_dict['currency'] = currency.id
                invoice_dict['invoice_address'] = party[0].address_get('delivery').id
                invoice_dict['party'] = hrp_shipment_return_lines['supply_name']
                invoice_dict['type'] = 'in'
                invoice_dict['accounting_date'] = None
                invoice_dict['state'] = 'draft'
                invoice_id = Invoice.create([invoice_dict])
                invoice = Invoice.search([('id', '=', invoice_id[0].id)])
                Invoice.validate_invoice(invoice)
                Invoice.validate_invoice(invoice)
                lv = {}
                lv['moves'] = [
                    [
                        u'create',
                        [
                            {
                                u'outgoing_audit': u'00',
                                u'origin': u'stock.inventory.line,-1',
                                u'product': hrp_shipment_return_lines['product'],
                                u'comment': hrp_shipment_return_lines['note'],
                                u'move_type': '102',
                                u'from_location': from_location,
                                u'invoice_lines': [
                                    [
                                        u'add',
                                        [
                                            invoice[0].lines[0].id
                                        ]
                                    ]
                                ],
                                u'planned_date': today,
                                u'company': Transaction().context.get('company'),
                                u'actual_return': hrp_shipment_return_lines['invoice_amount'],
                                u'unit_price': hrp_shipment_return_lines['cost_price'],
                                u'currency': currency.id,
                                u'to_location': party[0].supplier_location,
                                u'lot': hrp_shipment_return_lines['lot'],
                                u'starts': u'05',
                                u'quantity': hrp_shipment_return_lines['quantity'],
                                u'uom': hrp_shipment_return_lines['retail_package'],
                            }
                        ]
                    ]
                ]
                lv['reference'] = hrp_shipment_return_lines['invoice_code']
                lv['number'] = Sequence.get_id(config1.shipment_in_return_sequence.id)
                lv['supplier'] = hrp_shipment_return_lines['supply_name']
                lv['delivery_address'] = party[0].address_get('delivery')
                lv['from_location'] = from_location
                lv['to_location'] = party[0].supplier_location
                lv['planned_date'] = today
                lv['effective_date'] = today
                lv['state'] = 'draft'
                lv['categories'] = data['start']['categories']
                lv['order_no'] = order_no[0].id
                ship = ShipmentInReturn.create([lv])
                shipment = ShipmentInReturn.search([('id', '=', ship[0].id)])
                ShipmentInReturn.wait(shipment)
                whether_move = Move.assign_try([Move(ship[0].moves[0].id)], grouping=('product', 'lot'))
                if not whether_move:
                    message += ship[0].moves[0].product.code + ship[0].moves[
                        0].product.name + u'-批次:' + Lot(
                        ship[0].moves[0].lot).number + u'实际数量有变,请删除该行项目后重新输入\n'
                    continue
            if message:
                self.raise_user_error(message)
        return action, {}


# 无采购订单入库
class ShipmentOrderLines(ModelView):
    "Shipment Order Lines"
    __name__ = "shipment_order_lines"
    _rec_name = 'ShipmentOrderLines'

    product_code = fields.Char('product_code', readonly=True)
    product_name = fields.Char('product_name', readonly=True)
    supply_name = fields.Many2One('party.party', 'Supply Name', readonly=True)
    product = fields.Many2One('product.product', 'Product')
    location = fields.Many2One('stock.location', 'location', domain=[('type', '=', 'warehouse')], )
    purchase_code = fields.Char('Purchase Code')
    manufacturers_describtion = fields.Char('Manufacturers Describtion', readonly=True, states=STATES)
    quantity = fields.Integer('Quantity', states=STATES)
    retail_package = fields.Many2One('product.uom', 'Retail Package', readonly=True, states=STATES)
    list_price = fields.Numeric('List Price', digits=(16, 2), states=STATES, readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 2), states=STATES, readonly=True)
    lot = fields.Many2One('stock.lot', 'Lot', context={
        'locations': [Eval('location')]}, states=STATES, domain=[
        ('product', '=', Eval('product')),
    ], )
    drug_specifications = fields.Char('Drug Speic', states=STATES, readonly=True)
    drug_approval_number = fields.Char('Drug Approval Number', states=STATES, readonly=True)
    why = fields.Selection([
        ('00', u'入库'),
        ('01', u'出库')
    ], 'Why')
    cause = fields.Selection([
        ('24', u'病人退费'),
        ('23', u'工作失误'),
        ('22', u'规格变更'),
        ('21', u'一品多规'),
        ('20', u'药品名称变更'),
        ('19', u'欠药病人不退'),
        ('18', u'盈亏误差'),
        ('17', u'入库错误'),
        ('16', u'近期药品'),
        ('15', u'处理破损药'),
        ('14', u'取未取药'),
        ('13', u'药剂科结余'),
        ('12', u'调批号'),
        ('11', u'科室换药'),
        ('10', u'原装破损'),
        ('09', u'科室基数'),
        ('08', u'损药换新'),
        ('07', u'新配制剂'),
        ('06', u'药品分装'),
        ('05', u'原料药消耗'),
        ('04', u'疫苗入库'),
        ('03', u'疫苗记帐'),
        ('02', u'疫苗支票'),
        ('01', u'退药'),
        ('00', u'正常'),
    ], 'Cause')


class ShipmentOrder(ModelView):
    "Shipment Order"
    __name__ = "shipment_order"

    supply_name = fields.Many2One('party.party', 'Supply Name', readonly=True)
    product = fields.Many2One('product.product', 'Product')
    location = fields.Many2One('stock.location', 'location', states={
        'readonly': Bool(Eval('shipment_order_lines')),
    }, domain=[('type', '=', 'warehouse')], )
    purchase_code = fields.Char('Purchase Code')
    manufacturers_describtion = fields.Char('Manufacturers Describtion', readonly=True, states=STATES)
    quantity = fields.Integer('Quantity', states=STATES)
    retail_package = fields.Many2One('product.uom', 'Retail Package', readonly=True, states=STATES)
    list_price = fields.Numeric('List Price', digits=(16, 4), states=STATES, readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), states=STATES, readonly=True)
    lot = fields.Many2One('stock.lot', 'Lot', states=STATES, context={
        'locations': [Eval('location')]}, domain=[
        If(Eval('pick_out') == 'return',
           [('product', '=', Eval('product')),
            ('id', 'in', Eval('lots'))],
           [('product', '=', Eval('product'))])],
                          depends=['product', 'lots', 'locations'])
    lots = fields.Function(
        fields.One2Many('stock.lot', None, 'Lots'),
        'on_change_with_lots')
    dom = fields.Function(fields.Date('DOM', states=STATES, readonly=True), 'get_dom', 'set_dom')
    exp_date = fields.Function(fields.Date('Exp Date', states=STATES, readonly=True), 'get_exp_date', 'set_exp_date')
    drug_specifications = fields.Char('Drug Speic', states=STATES, readonly=True)
    drug_approval_number = fields.Char('Drug Approval Number', states=STATES, readonly=True)
    shipment_order_lines = fields.One2Many('shipment_order_lines', None, 'Shipment Order Lines')
    shipment_order = fields.Boolean('Shipment Order')
    pick_out = fields.Selection([
        ('purchase', u'入库'),
        ('return', u'出库')
    ], 'Pick Out', states={
        'readonly': Bool(Eval('shipment_order_lines'))})
    why = fields.Selection([
        ('00', u'入库'),
        ('01', u'出库')
    ], 'Why')
    cause = fields.Selection([
        ('24', u'病人退费'),
        ('23', u'工作失误'),
        ('22', u'规格变更'),
        ('21', u'一品多规'),
        ('20', u'药品名称变更'),
        ('19', u'欠药病人不退'),
        ('18', u'盈亏误差'),
        ('17', u'入库错误'),
        ('16', u'近期药品'),
        ('15', u'处理破损药'),
        ('14', u'取未取药'),
        ('13', u'药剂科结余'),
        ('12', u'调批号'),
        ('11', u'科室换药'),
        ('10', u'原装破损'),
        ('09', u'科室基数'),
        ('08', u'损药换新'),
        ('07', u'新配制剂'),
        ('06', u'药品分装'),
        ('05', u'原料药消耗'),
        ('04', u'疫苗入库'),
        ('03', u'疫苗记帐'),
        ('02', u'疫苗支票'),
        ('01', u'退药'),
        ('00', u'正常'),
    ], 'Cause', required=True)

    @staticmethod
    def default_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_warehouse()

    @fields.depends('location', 'product')
    def on_change_with_lots(self, name=None):
        if self.location and self.product:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.location.id], [self.product.id], with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value > 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('quantity', 'list_price', 'location', 'product', 'pick_out', 'lot', 'retail_package')
    def on_change_quantity(self, name=None):
        if self.quantity and self.pick_out == 'return' and self.lot:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([self.location.id], [self.product.id], with_childs=True,
                                                               grouping=('product', 'lot'))
                quantity = warehouse_quant[(self.location.id, self.product.id, self.lot.id)]
                factor = round((self.product.default_uom.factor * self.retail_package.rate), 3)  # 单位换算
                quantity_all = self.quantity * factor
                if quantity < quantity_all:
                    self.quantity = 0
                    self.raise_user_error(u'数量应小于%s%s' % (quantity, self.product.default_uom.name))
                self.retail_amount = int(quantity_all) * int(self.list_price)

    @fields.depends('shipment_order', 'product', 'drug_specifications', 'cost_price', 'list_price', 'location',
                    'pick_out',
                    'drug_approval_number', 'manufacturers_describtion', 'quantity', 'retail_package', 'lot', 'why',
                    'cause')
    def on_change_shipment_order(self, name=None):
        if self.shipment_order == True and self.product != None and self.retail_package != None and self.lot != None:
            if self.pick_out == 'return':
                Date = Pool().get('ir.date')
                Product = Pool().get('product.product')
                with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                    warehouse_quant = Product.products_by_location([self.location.id], [self.product.id],
                                                                   with_childs=True, grouping=('product', 'lot'))
                    number = warehouse_quant[(self.location.id, self.product.id, self.lot.id)]
                    if number < self.quantity:
                        self.raise_user_error(u'所选数量超过%s' % number)
            list = []
            dict = {}
            dict['product'] = self.product.id
            dict['product_code'] = self.product.code
            dict['product_name'] = self.product.name
            dict['location'] = self.location.id
            dict['drug_specifications'] = self.drug_specifications
            dict['quantity'] = self.quantity
            dict['retail_package'] = self.retail_package.id
            dict['lot'] = self.lot.id
            dict['cost_price'] = self.cost_price * decimal.Decimal(str(self.quantity))
            dict['list_price'] = self.list_price * decimal.Decimal(str(self.quantity))
            dict['drug_approval_number'] = self.drug_approval_number
            dict['manufacturers_describtion'] = self.manufacturers_describtion
            dict['why'] = self.why
            dict['cause'] = self.cause
            list.append(dict)
            self.shipment_order_lines = list
            self.product = None
            self.shipment_order = None
            self.drug_specifications = None
            self.drug_approval_number = None
            self.manufacturers_describtion = None
            self.quantity = None
            self.retail_package = None
            self.lot = None
            self.cost_price = None
            self.list_price = None

    @fields.depends('product')
    def on_change_product(self, name=None):
        if self.product:
            pool = Pool()
            try:
                product_templates = pool.get('product.template')
                product_template = product_templates.search([
                    ("id", "=", int(self.product.template))
                ])
                manufacturers_describtion = product_template[0].manufacturers_describtion
                retail_package = product_template[0].default_uom.id
                drug_approval_number = product_template[0].approval_number
                drug_specifications = product_template[0].drug_specifications
                self.list_price = product_template[0].list_price
                self.cost_price = product_template[0].cost_price
                self.drug_specifications = drug_specifications
                self.drug_approval_number = drug_approval_number
                self.retail_package = retail_package
                self.manufacturers_describtion = manufacturers_describtion
            except:
                return None

    @fields.depends('lot', 'pick_out')
    def on_change_lot(self, name=None):
        Date = Pool().get('ir.date')
        if self.lot:
            if self.lot.shelf_life_expiration_date < Date.today():
                self.raise_user_error(u'所选批次已过期，请确定。')
            self.dom = self.lot.date_of_production
            self.exp_date = self.lot.shelf_life_expiration_date

    def get_dom(self, name):
        if self.lot:
            return self.lot.date_of_production

    def get_exp_date(self, name):
        if self.lot:
            return self.lot.shelf_life_expiration_date

    @classmethod
    def set_dom(cls, set_name, name, value):
        pass

    @classmethod
    def set_exp_date(cls, set_exp_date, name, value):
        pass


class CreateShipmentOrder(Wizard):
    'Greate Purchase Shipment'
    __name__ = 'create_shipment_order'
    start = StateView('shipment_order',
                      'hrp_shipment.shipment_order_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_create_shipment_order')

    def do_create_(self, action):
        Party = Pool().get('party.party')
        Product = Pool().get('product.product')
        OrderNo = Pool().get('order_no')
        Move = Pool().get('stock.move')
        Lot = Pool().get('stock.lot')
        ShipmentInReturn = Pool().get('stock.shipment.in.return')
        ShipmentIn = Pool().get('stock.shipment.in')
        Location = Pool().get('stock.location')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        Company = Pool().get('company.company')
        company = Company.search([('id', '=', Transaction().context['company'])])
        currency = company[0].currency
        Date = Pool().get('ir.date')
        today = str(Date.today())
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        if data != {}:
            message = ''
            for shipment_order_lines in data['start']['shipment_order_lines']:
                if shipment_order_lines != None:
                    party = Party.search([('id', '=', config.default_.id)])
                    location = Location.search([('id', '=', shipment_order_lines['location'])])
                    lv = [
                        {
                            u'reference': u'',
                            u'planned_date': today,
                            u'company': Transaction().context.get('company'),
                            u'effective_date': today,
                            u'cause': shipment_order_lines['cause'],
                            u'supplier': config.default_.id,
                        }
                    ]

                    if data['start']['pick_out'] == 'purchase':
                        lv[0][u'contact_address'] = party[0].address_get('delivery').id
                        lv[0][u'warehouse'] = shipment_order_lines['location']
                        lv[0][u'inventory_moves'] = []
                        incoming_moves = [
                            [
                                u'create',
                                [
                                    {
                                        u'outgoing_audit': u'02',
                                        u'product': shipment_order_lines['product'],
                                        u'to_location': location[0].input_location.id,
                                        u'from_location': party[0].supplier_location.id,
                                        u'invoice_lines': [],
                                        u'starts': u'05',
                                        u'move_type': '501',
                                        u'company': Transaction().context.get('company'),
                                        u'list_price': shipment_order_lines['list_price'],
                                        u'cost_price': shipment_order_lines['cost_price'],
                                        u'unit_price': shipment_order_lines['cost_price'],
                                        u'currency': currency.id,
                                        u'lot': shipment_order_lines['lot'],
                                        u'planned_date': today,
                                        u'uom': shipment_order_lines['retail_package'],
                                        u'origin': u'stock.inventory.line,-1',
                                        u'quantity': shipment_order_lines['quantity']
                                    }
                                ]
                            ]
                        ]
                        lv[0][u'moves'] = incoming_moves
                        # lv[0][u'incoming_moves'] = incoming_moves
                        lv[0][u'in_storage'] = today  # Sequence.get_id(config.in_storage)
                        shipments = ShipmentIn.create(lv)
                        shipment = ShipmentIn.search([('id', '=', shipments[0].id)])
                        ShipmentIn.receive(shipment)
                        ShipmentIn.done(shipment)
                    else:
                        lv[0]['number'] = today  # Sequence.get_id(config1.shipment_in_return_sequence.id)
                        lv[0][u'delivery_address'] = party[0].address_get('delivery').id
                        lv[0][u'to_location'] = party[0].supplier_location.id
                        lv[0][u'from_location'] = location[0].storage_location.id
                        moves = [
                            [
                                u'create',
                                [
                                    {
                                        u'outgoing_audit': u'02',
                                        u'product': shipment_order_lines['product'],
                                        u'to_location': party[0].supplier_location.id,
                                        u'from_location': location[0].storage_location.id,
                                        u'invoice_lines': [],
                                        u'starts': u'05',
                                        u'move_type': '502',
                                        u'list_price': shipment_order_lines['list_price'],
                                        u'cost_price': shipment_order_lines['cost_price'],
                                        u'company': Transaction().context.get('company'),
                                        u'unit_price': shipment_order_lines['cost_price'],
                                        u'currency': currency.id,
                                        u'lot': shipment_order_lines['lot'],
                                        u'planned_date': today,
                                        u'uom': shipment_order_lines['retail_package'],
                                        u'origin': u'stock.inventory.line,-1',
                                        u'quantity': shipment_order_lines['quantity']
                                    }
                                ]
                            ]
                        ]
                        order_no = OrderNo.create([{'number': '00', 'time': today, 'order_category': 'outbound'}])
                        lv[0][u'moves'] = moves
                        lv[0][u'order_no'] = order_no[0].id
                        lv[0][u'categories'] = Product(shipment_order_lines['product']).categories[0].id
                        lv[0]['state'] = 'draft'
                        ship = ShipmentInReturn.create(lv)
                        whether_move = Move.assign_try([Move(ship[0].moves[0].id)], grouping=('product', 'lot'))
                        if not whether_move:
                            message += ship[0].moves[0].product.code + ship[0].moves[
                                0].product.name + u'-批次:' + Lot(
                                ship[0].moves[0].lot).number + u'实际数量有变,请删除该行项目后重新输入\n'
                            continue
                        shipment = ShipmentInReturn.search([('id', '=', ship[0].id)])
                        ShipmentInReturn.wait(shipment)
                        ShipmentInReturn.assign(shipment)
                        ShipmentInReturn.done(shipment)
            if message:
                self.raise_user_error(message)
        return action, {}


# 手工消耗

class HrpSaleLines(ModelView):
    "Hrp Sale Lines"
    __name__ = "hrp_sale_lines"
    party = fields.Many2One('party.party', 'department', domain=[
        ('type_', '=', 'client'),
        ('id', 'not in', [1])
    ])
    code = fields.Char('code')
    describe = fields.Char('describe')
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Integer('Quantity')
    retail_package = fields.Many2One('product.uom', 'Retail Package', readonly=True)
    list_price = fields.Numeric('List Price', digits=(16, 2), readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)
    lot = fields.Many2One('stock.lot', 'Lot', states=STATES, domain=[
        ('product', '=', Eval('product')),
    ], )
    exp_date = fields.Function(fields.Date('Exp Date', readonly=True), 'get_exp_date', 'set_exp_date')
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    location = fields.Many2One('stock.location', 'location', domain=[('type', '=', 'warehouse')], )
    manufacturers_describtion = fields.Char('Manufacturers Describtion', readonly=True)


class HrpSale(ModelView):
    "Hrp Sale"
    __name__ = "hrp_sale"

    party = fields.Many2One('party.party', 'department', domain=[
        ('type_', '=', 'client'),
        ('id', 'not in', [1, 3])
    ], states={
        'readonly': Bool(Eval('sale_lines')),
    })
    products = fields.Function(
        fields.One2Many('product.product', None, 'Product'),
        'on_change_with_product')
    product = fields.Many2One('product.product', 'Product', domain=[
        ('id', 'in', Eval('products')),
    ], depends=['products'])
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    retail_package = fields.Many2One('product.uom', 'Retail Package',
                                     domain=[
                                         ('category', '=', Eval('product_uom_category')),
                                     ],
                                     depends=['product_uom_category'],
                                     readonly=False, required=False)
    quantity = fields.Integer('Quantity')
    lots = fields.Function(fields.One2Many('stock.lot', None, 'Lots'), 'on_change_with_lots')
    lot = fields.Many2One('stock.lot', 'Lot', context={
        'locations': [Eval('location')],
    }, domain=[('product', '=', Eval('product'))],
                          depends=['location', 'lots'])
    describe = fields.Char('describe', readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    location_default = fields.Function(fields.Many2One('stock.location', 'location'), 'on_change_with_location_default')
    location = fields.Many2One('stock.location', 'location', domain=[
        ('id', '=', [Eval('location_default')])
    ], readonly=True, depends=['location_default', 'sale_lines'])
    sale_lines = fields.One2Many('hrp_sale_lines', None, 'Hrp Sale Lines')
    is_sale = fields.Boolean('Is_Sale')
    pick_out = fields.Selection([
        ('sale', u'发药'),
        ('return', u'退药')
    ], 'Pick Out', states={
        'readonly': Bool(Eval('sale_lines')),
    })

    # @staticmethod
    # def default_location():
    #     UserId = Pool().get('hrp_internal_delivery.test_straight')
    #     return UserId.get_user_id()

    @fields.depends('location', 'product', 'pick_out')
    def on_change_with_lots(self, name=None):
        if self.location and self.product:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location([self.location.id], [self.product.id], with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value >= 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('location', 'pick_out')
    def on_change_with_products(self, name=None):
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        Date = Pool().get('ir.date')
        Product = Pool().get('product.product')
        if self.pick_out and self.pick_out == 'sale':
            with Transaction().set_context(stock_date_end=Date.today()):
                location = self.location.id
                if self.location.id == warehouse:
                    location = config.warehouse.freeze_location.id
                ces = Product.products_by_location([location], with_childs=True)
                lists = ces.keys()
                list_c = []
                for i in lists:
                    if ces[i] <= 0.0:
                        list_c.append(i)
                for g in list_c:
                    lists.remove(g)
                product_ids = []
                for g in lists:
                    product_ids.append(g[1])

            return product_ids
        else:
            product = Product.search([])
            product_ids = [i.id for i in product]
            return product_ids

    @fields.depends('pick_out')
    def on_change_with_location_default(self, name=None):
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        if self.pick_out == 'sale' and UserId.get_user_warehouse() == config.warehouse.id:
            return config.warehouse.freeze_location.id
        else:
            return UserId.get_user_warehouse()

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('product', 'lot')
    def on_change_product(self, name=None):
        if self.product:
            pool = Pool()
            try:
                product_templates = pool.get('product.template')
                product_template = product_templates.search([
                    ("id", "=", int(self.product.template))
                ])
                self.describe = product_template[0].name
                self.drug_specifications = product_template[0].drug_specifications
                self.retail_package = product_template[0].default_uom.id
            except:
                return None
        else:
            self.describe = None
            self.drug_specifications = None
            self.retail_package = None
            self.lot = None

    @fields.depends('product', 'location', 'quantity', 'pick_out')
    def on_change_pick_out(self):
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        if self.pick_out == 'sale' and UserId.get_user_warehouse() == config.warehouse.id:
            self.location = config.warehouse.freeze_location.id
        else:
            self.location = UserId.get_user_warehouse()
        HrpSale.on_change_with_products(self)

    @fields.depends('product', 'location', 'quantity', 'pick_out', 'lot', 'retail_package')
    def on_change_quantity(self, name=None):
        pass
        # if self.quantity and self.pick_out == 'sale':
        #     Uom = Pool().get('product.uom')
        #     Date = Pool().get('ir.date')
        #     Product = Pool().get('product.product')
        #     with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):# 查看具体库下面的批次对应的数量
        #         pbl = Product.products_by_location([self.location.id],[self.product.id], with_childs=True)
        #         quantity = Uom.compute_qty(self.product.default_uom, pbl[(self.location.id, self.product.id)],self.retail_package )# 单位换算factor
        #         if quantity < self.quantity:
        #             self.quantity = 0
        #             self.raise_user_error( u'数量应小于%s%s' % (quantity,self.retail_package.name))
        # if self.quantity and self.pick_out == 'return':
        #     if not self.lot:
        #         self.raise_user_error(u'批次为必填项')

    @fields.depends('is_sale', 'product', 'drug_specifications', 'describe', 'location', 'quantity', 'retail_package',
                    'lot', 'pick_out', 'party')
    def on_change_is_sale(self, name=None):
        Lot = Pool().get('stock.lot')
        Uom = Pool().get('product.uom')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        getcontext().prec = 6
        try:
            if self.is_sale == True and self.product != None and self.retail_package != None and self.party != None:
                if self.pick_out == 'return':
                    list = []
                    dict = {}
                    dict['product'] = self.product.id
                    dict['code'] = self.product.code
                    dict['describe'] = self.product.name
                    dict['location'] = self.location.id
                    dict['drug_specifications'] = self.drug_specifications
                    dict['quantity'] = self.quantity
                    dict['retail_package'] = self.retail_package.id
                    dict['lot'] = self.lot.id
                    dict['location'] = self.location.id
                    dict['party'] = self.party.id
                    if self.product.default_uom != self.retail_package:
                        dict['cost_price'] = Uom.compute_price(self.product.default_uom, self.product.cost_price,
                                                               self.retail_package) * decimal.Decimal(
                            str(self.quantity))
                        dict['list_price'] = Uom.compute_price(self.product.default_uom, self.product.list_price,
                                                               self.retail_package) * decimal.Decimal(
                            str(self.quantity))
                    else:
                        dict['cost_price'] = self.product.cost_price * decimal.Decimal(str(self.quantity))
                        dict['list_price'] = self.product.list_price * decimal.Decimal(str(self.quantity))
                    dict['exp_date'] = self.lot.shelf_life_expiration_date
                    dict['manufacturers_describtion'] = self.product.manufacturers_describtion
                    list.append(dict)
                    self.sale_lines = list
                    self.product = None
                    self.drug_specifications = None
                    self.product = None
                    self.quantity = None
                    self.drug_specifications = None
                    self.lot = None
                    self.retail_package = None
                    self.is_sale = False
                else:
                    Date = Pool().get('ir.date')
                    Product = Pool().get('product.product')
                    location = self.location.id
                    if self.location.id == warehouse:
                        location = config.warehouse.freeze_location.id
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([location], [self.product.id],
                                                                       with_childs=True, grouping=('product', 'lot'))
                        numbers = 0
                        for key, value in warehouse_quant.items():
                            numbers += Uom.compute_qty(self.product.default_uom, value, self.retail_package)
                        if numbers < self.quantity:
                            self.raise_user_error(u'数量应小于%s%s' % (numbers, self.retail_package.name))
                    done_list = []
                    lists = []
                    num = 0
                    number = 0
                    Date = Pool().get('ir.date')
                    Product = Pool().get('product.product')
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([location], [self.product.id], with_childs=True,
                                                                       grouping=('product', 'lot'))
                        for key, value in warehouse_quant.items():
                            if value != 0.0:
                                if key[-1] != None:
                                    lists.append(key[-1])
                        lens = len(lists)
                        lot_list = []
                        for lot_id in lists:
                            search_lot = Lot.search([
                                ('id', '=', lot_id)
                            ])
                            for lot in search_lot:
                                dict_sorted = {}
                                expiraton = lot.shelf_life_expiration_date
                                dict_sorted['id'] = lot_id
                                dict_sorted['time_stamp'] = str(expiraton)
                                lot_list.append(dict_sorted)
                        lots_list = sorted(lot_list, key=operator.itemgetter('time_stamp'))
                        for lot_len in range(lens):
                            done_id = lots_list[lot_len]['id']
                            done_list.append(done_id)
                        len_lot = len(done_list)
                        for id_lot in range(len_lot):
                            lot_quants = warehouse_quant[(location, self.product.id, done_list[id_lot])]  # 对应批次的库存数量
                            lot_quant = Uom.compute_qty(self.product.default_uom, lot_quants, self.retail_package)
                            num += 1  # 满足请领数量的批次
                            number += lot_quant
                            if number >= self.quantity:  # 请领数量与该批次的库存数对比
                                break
                        list = []
                        for lo in range(num):
                            if num == 1:
                                list = []
                                dict = {}
                                dict['product'] = self.product.id
                                dict['code'] = self.product.code
                                dict['describe'] = self.product.name
                                dict['location'] = self.location.id
                                dict['drug_specifications'] = self.drug_specifications
                                dict['quantity'] = self.quantity
                                dict['party'] = self.party.id
                                dict['retail_package'] = self.retail_package.id
                                dict['lot'] = done_list[lo]
                                lot = Lot.search([('id', '=', done_list[lo])])
                                if self.product.default_uom != self.retail_package:
                                    dict['cost_price'] = Uom.compute_price(self.product.default_uom,
                                                                           self.product.cost_price,
                                                                           self.retail_package) * decimal.Decimal(
                                        str(self.quantity))
                                    dict['list_price'] = Uom.compute_price(self.product.default_uom,
                                                                           self.product.list_price,
                                                                           self.retail_package) * decimal.Decimal(
                                        str(self.quantity))
                                else:
                                    dict['cost_price'] = self.product.cost_price * decimal.Decimal(str(self.quantity))
                                    dict['list_price'] = self.product.list_price * decimal.Decimal(str(self.quantity))
                                dict['exp_date'] = lot[0].shelf_life_expiration_date
                                dict['manufacturers_describtion'] = self.product.manufacturers_describtion
                                list.append(dict)
                                self.sale_lines = list
                            else:
                                if lo == 0:
                                    lot_quant_ones = warehouse_quant[(self.location.id, self.product.id, done_list[lo])]
                                    lot_quant_one = Uom.compute_qty(self.product.default_uom, lot_quant_ones,
                                                                    self.retail_package)
                                    dict = {}
                                    dict['product'] = self.product.id
                                    dict['code'] = self.product.code
                                    dict['describe'] = self.product.name
                                    dict['location'] = self.location.id
                                    dict['drug_specifications'] = self.drug_specifications
                                    dict['quantity'] = lot_quant_one
                                    dict['party'] = self.party.id
                                    dict['retail_package'] = self.retail_package.id
                                    dict['lot'] = done_list[lo]
                                    lot = Lot.search([('id', '=', done_list[lo])])
                                    if self.product.default_uom != self.retail_package:
                                        dict['cost_price'] = Uom.compute_price(self.product.default_uom,
                                                                               self.product.cost_price,
                                                                               self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                        dict['list_price'] = Uom.compute_price(self.product.default_uom,
                                                                               self.product.list_price,
                                                                               self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                    else:
                                        dict['cost_price'] = self.product.cost_price * decimal.Decimal(
                                            str(self.quantity))
                                        dict['list_price'] = self.product.list_price * decimal.Decimal(
                                            str(self.quantity))
                                    dict['exp_date'] = lot[0].shelf_life_expiration_date
                                    dict['manufacturers_describtion'] = self.product.manufacturers_describtion
                                    list.append(dict)
                                elif lo == num - 1:
                                    lot_quant_twos = warehouse_quant[(self.location.id, self.product.id, done_list[lo])]
                                    lot_quant_two = Uom.compute_qty(self.product.default_uom, lot_quant_twos,
                                                                    self.retail_package)
                                    Quantity = lot_quant_two - (number - self.quantity)
                                    dict_s = {}
                                    dict_s['product'] = self.product.id
                                    dict_s['code'] = self.product.code
                                    dict_s['describe'] = self.product.name
                                    dict_s['location'] = self.location.id
                                    dict_s['drug_specifications'] = self.drug_specifications
                                    dict_s['quantity'] = Quantity
                                    dict_s['party'] = self.party.id
                                    dict_s['retail_package'] = self.retail_package.id
                                    dict_s['lot'] = done_list[lo]
                                    lot = Lot.search([('id', '=', done_list[lo])])
                                    if self.product.default_uom != self.retail_package:
                                        dict_s['cost_price'] = Uom.compute_price(self.product.default_uom,
                                                                                 self.product.cost_price,
                                                                                 self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                        dict_s['list_price'] = Uom.compute_price(self.product.default_uom,
                                                                                 self.product.list_price,
                                                                                 self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                    else:
                                        dict_s['cost_price'] = self.product.cost_price * decimal.Decimal(
                                            str(self.quantity))
                                        dict_s['list_price'] = self.product.list_price * decimal.Decimal(
                                            str(self.quantity))
                                    dict_s['exp_date'] = lot[0].shelf_life_expiration_date
                                    dict_s['manufacturers_describtion'] = self.product.manufacturers_describtion
                                    list.append(dict_s)
                                else:
                                    lot_quant_threes = warehouse_quant[
                                        (self.location.id, self.product.id, done_list[lo])]
                                    lot_quant_three = Uom.compute_qty(self.product.default_uom, lot_quant_threes,
                                                                      self.retail_package)
                                    dict_t = {}
                                    dict_t['product'] = self.product.id
                                    dict_t['code'] = self.product.code
                                    dict_t['describe'] = self.product.name
                                    dict_t['location'] = self.location.id
                                    dict_t['party'] = self.party.id
                                    dict_t['drug_specifications'] = self.drug_specifications
                                    dict_t['quantity'] = lot_quant_three
                                    dict_t['retail_package'] = self.retail_package.id
                                    dict_t['lot'] = done_list[lo]
                                    lot = Lot.search([('id', '=', done_list[lo])])
                                    if self.product.default_uom != self.retail_package:
                                        dict_t['cost_price'] = Uom.compute_price(self.product.default_uom,
                                                                                 self.product.cost_price,
                                                                                 self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                        dict_t['list_price'] = Uom.compute_price(self.product.default_uom,
                                                                                 self.product.list_price,
                                                                                 self.retail_package) * decimal.Decimal(
                                            str(self.quantity))
                                    else:
                                        dict_t['cost_price'] = self.product.cost_price * decimal.Decimal(
                                            str(self.quantity))
                                        dict_t['list_price'] = self.product.list_price * decimal.Decimal(
                                            str(self.quantity))
                                    dict_t['exp_date'] = lot[0].shelf_life_expiration_date
                                    dict_t['manufacturers_describtion'] = self.product.manufacturers_describtion
                                    list.append(dict_t)
                        self.sale_lines = list
                        self.product = None
                        self.quantity = None
                        self.lot = None
                        self.drug_specifications = None
                        self.retail_package = None
                        self.is_sale = False
        except AttributeError:
            self.raise_user_error(u'请先填写批次')


class HrpCreateSale(Wizard):
    'Hrp Create Sale'
    __name__ = 'hrp_create_sale'
    start = StateView('hrp_sale',
                      'hrp_shipment.hrp_sale_view_form', [
                          Button(u'取消', 'end', 'tryton-cancel'),
                          Button(u'打印', 'print_', 'tryton-print', default=True),
                      ])
    print_ = StateReport('hrp_sale_report')

    def do_print_(self, action):
        Party = Pool().get('party.party')
        Uom = Pool().get('product.uom')
        Lot = Pool().get('stock.lot')
        OrderNo = Pool().get('order_no')
        Product = Pool().get('product.product')
        ShipmentInternal = Pool().get('stock.shipment.internal')
        ShipmentOut = Pool().get('stock.shipment.out')
        ShipmentOutReturn = Pool().get('stock.shipment.out.return')
        Sale = Pool().get('sale.sale')
        Location = Pool().get('stock.location')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        Configs = Pool().get('sale.configuration')
        configs = Configs(1)
        shipment_method = configs.sale_shipment_method
        invoice_method = configs.sale_invoice_method
        Company = Pool().get('company.company')
        company = Company.search([('id', '=', Transaction().context['company'])])
        currency = company[0].currency
        Date = Pool().get('ir.date')
        Move = Pool().get('stock.move')
        today = str(Date.today())
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        if data != {}:
            message = ''
            shipment_squence = OrderNo.search([('location', '=', data['start']['location']),
                                               ('order_category', 'in', ['902', 'sale_return', 'sale_purchase'])],
                                              order=[["id", "DESC"]])
            try:
                if shipment_squence and int(shipment_squence[0].number[2:8]) == int(
                        time.strftime('%Y%m', time.localtime())):
                    squence = Location(data['start']['location']).code + 'K' \
                              + time.strftime('%Y%m', time.localtime()) \
                              + str(int(shipment_squence[0].number[9:]) + 1).zfill(4)
                else:
                    squence = Location(data['start']['location']).code \
                              + 'K' + time.strftime('%Y%m', time.localtime()) + '1'.zfill(4)
            except:
                squence = Location(data['start']['location']).code + 'K' + time.strftime(
                    '%Y%m', time.localtime()) + '1'.zfill(4)
            order_no = {'number': squence, 'time': today, 'location': data['start']['location']}
            if data['start']['pick_out'] == 'sale':
                order_no['order_category'] = 'sale_purchase'
            if data['start']['pick_out'] == 'return':
                order_no['order_category'] = 'sale_return'
            OrderNo.create([order_no])
            for sale_lines in data['start']['sale_lines']:
                # try:
                if True:
                    if sale_lines is not None:
                        sale_location = sale_lines['location']
                        if data['start']['location'] == config.warehouse.freeze_location.id:
                            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                                pbl = Product.products_by_location([config.warehouse.freeze_location.id],
                                                                   [sale_lines['product']],
                                                                   with_childs=True, grouping=('product', 'lot'))
                                assign_quantity = pbl[
                                    (config.warehouse.freeze_location.id, sale_lines['product'], sale_lines['lot'])]
                            if assign_quantity < sale_lines['quantity']:
                                self.raise_user_error(u'可用数量不足%s%s') % (assign_quantity, sale_lines['retail_package'])
                            return_shipment = OrderNo.create(
                                [{'number': squence, 'time': today, 'location': sale_lines['location'],
                                  'order_category': '902'}])
                            internal = {}
                            internal['company'] = 1
                            internal['to_location'] = config.warehouse.storage_location.id
                            internal['from_location'] = config.warehouse.freeze_location.id
                            internal['return_shipment'] = return_shipment[0].id
                            internal['state'] = u'draft'
                            list = []
                            dict = {}
                            dict['origin'] = None  # each['origin']
                            dict['to_location'] = config.warehouse.storage_location.id
                            dict['actual_return'] = sale_lines['cost_price']
                            dict['product'] = sale_lines['product']
                            dict['list_price'] = sale_lines['list_price'].quantize(Decimal('0.00'))
                            dict['cost_price'] = sale_lines['cost_price'].quantize(Decimal('0.00'))
                            dict['from_location'] = config.warehouse.freeze_location.id
                            dict['invoice_lines'] = ()
                            dict['company'] = Transaction().context.get('company')
                            dict['unit_price'] = sale_lines['list_price']
                            dict['lot'] = sale_lines['lot']  # 产品批次
                            dict['uom'] = sale_lines['retail_package']  # 产品单位
                            dict['move_type'] = '902'
                            dict['quantity'] = sale_lines['quantity']
                            list.append(dict)
                            internal['moves'] = [['create', list]]
                            internal['planned_date'] = today
                            Internal = ShipmentInternal.create([internal])
                            ShipmentInternal.wait(Internal)
                            ShipmentInternal.assign_try(Internal)
                            ShipmentInternal.done(Internal)
                            sale_location = warehouse
                        party = Party.search([('id', '=', sale_lines['party'])])
                        location = Location.search([('id', '=', sale_lines['location'])])
                        if data['start']['pick_out'] == 'return':
                            incoming_moves = [
                                [
                                    u'create',
                                    [
                                        {
                                            u'comment': u'',
                                            u'outgoing_audit': u'00',
                                            u'product': sale_lines['product'],
                                            u'to_location': location[0].input_location.id,
                                            u'from_location': party[0].customer_location.id,
                                            u'invoice_lines': [],
                                            u'starts': u'05',
                                            u'party': data['start']['party'],
                                            u'move_type': 'Z07',
                                            u'company': Transaction().context.get('company'),
                                            u'actual_return': sale_lines['cost_price'],
                                            u'cost_price': sale_lines['list_price'].quantize(Decimal('0.00')),
                                            u'list_price': sale_lines['list_price'].quantize(Decimal('0.00')),
                                            u'unit_price': sale_lines['list_price'].quantize(Decimal('0.00')),
                                            u'currency': currency.id,
                                            u'reason': '00',
                                            u'lot': sale_lines['lot'],
                                            u'planned_date': today,
                                            u'uom': sale_lines['retail_package'],
                                            u'origin': u'sale.line,-1',
                                            u'quantity': sale_lines['quantity']
                                        }
                                    ]
                                ]
                            ]
                            lv = [
                                {
                                    u'number': squence,
                                    u'customer': sale_lines['party'],
                                    u'delivery_address': party[0].address_get('delivery').id,
                                    u'reference': u'',
                                    u'planned_date': today,
                                    u'company': Transaction().context.get('company'),
                                    u'moves': incoming_moves,
                                    u'warehouse': sale_lines['location'],
                                    u'effective_date': today,
                                    u'inventory_moves': []
                                }
                            ]
                            shipmeng_out_returns = ShipmentOutReturn.create(lv)
                            shipmeng_out_return = ShipmentOutReturn.search([('id', '=', shipmeng_out_returns[0].id)])
                            ShipmentOutReturn.receive(shipmeng_out_return)
                            ShipmentOutReturn.done(shipmeng_out_return)
                        else:
                            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                                pbl = Product.products_by_location([sale_lines['location']], [sale_lines['product']],
                                                                   with_childs=True, grouping=('product', 'lot'))
                                forecast_quantity = pbl[
                                    (sale_lines['location'], sale_lines['product'], sale_lines['lot'])]

                            lvc = [
                                {
                                    u'number': squence,
                                    u'comment': u'',
                                    u'origin': u'sale.sale,-1',
                                    u'shipment_party': None,
                                    u'reference': u'',
                                    u'payment_term': party[0].supplier_payment_term.id,
                                    u'company': Transaction().context.get('company'),
                                    u'lines': [
                                        [
                                            u'create',
                                            [
                                                {
                                                    u'product': sale_lines['product'],
                                                    u'description': u' ',
                                                    u'sequence': 1,
                                                    u'taxes': [],
                                                    u'note': u'',
                                                    u'unit_price': sale_lines['list_price'].quantize(Decimal('0.00')),
                                                    u'type': u'line',
                                                    u'unit': sale_lines['retail_package'],
                                                    u'quantity': sale_lines['quantity']
                                                }
                                            ]
                                        ]
                                    ],
                                    u'invoice_method': invoice_method,
                                    u'currency': currency.id,
                                    u'sale_date': today,
                                    u'invoice_address': party[0].address_get('delivery').id,
                                    u'warehouse': sale_location,
                                    u'party': sale_lines['party'],
                                    u'shipment_address': party[0].address_get('delivery').id,
                                    u'shipment_method': shipment_method,
                                    u'description': u''
                                }
                            ]
                            sales = Sale.create(lvc)
                            sale = Sale.search([('id', '=', sales[0].id)])
                            Sale.quote(sale)
                            Sale.confirm(sale)
                            Sale.process(sale)
                            shipment_outs = ShipmentOut.search([('state', '=', 'waiting')])
                            ShipmentOut.write(shipment_outs, {'number': squence})
                            movess = Move.search([('id', '=', shipment_outs[0].outgoing_moves[0].id)])
                            Move.write(movess, {'lot': sale_lines['lot'],
                                                'move_type': 'Z08',
                                                'party': data['start']['party'],
                                                'cost_price': sale_lines['cost_price'].quantize(Decimal('0.00')),
                                                'list_price': sale_lines['list_price'].quantize(Decimal('0.00'))})
                            moves1 = Move.search([('id', '=', (shipment_outs[0].outgoing_moves[0].id) + 1)])
                            Move.write(moves1, {'lot': sale_lines['lot'],
                                                'move_type': 'Z08',
                                                'party': data['start']['party'],
                                                'cost_price': sale_lines['cost_price'].quantize(Decimal('0.00')),
                                                'list_price': sale_lines['list_price'].quantize(Decimal('0.00'))})
                            moves = Move.search([('id', '=', (shipment_outs[0].outgoing_moves[0].id) + 2)])
                            Move.write(moves, {'lot': sale_lines['lot'],
                                               'move_type': 'Z08',
                                               'party': data['start']['party'],
                                               'cost_price': sale_lines['cost_price'].quantize(Decimal('0.00')),
                                               'list_price': sale_lines['list_price'].quantize(Decimal('0.00'))})
                            whether_move = Move.assign_try(moves1, grouping=('product', 'lot'))
                            if not whether_move:
                                message += sale_lines['code'] + sale_lines['describe'] + u'-批次:' + Lot(
                                    sale_lines['lot']).number + u'当前可用数量为' + str(forecast_quantity) + Uom(
                                    sale_lines['retail_package']).name + u',请删除该行项目后重新输入\n'
                                continue
                            ShipmentOut.assign(shipment_outs)
                            ShipmentOut.assign_try(shipment_outs)
                            ShipmentOut.pack(shipment_outs)
                            ShipmentOut.done(shipment_outs)
                            # except:
                            #     continue
            if message:
                self.raise_user_error(message)
        return action, data


class HrpSaleReport(Report):
    """HrpSaleReport"""
    __name__ = 'hrp_sale_report'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(HrpSaleReport, cls).get_context(records, {})
        return report_context
