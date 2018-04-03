# coding:utf-8
import decimal
from decimal import Decimal

import time

from trytond.model import ModelView, fields, Workflow, ModelSQL
from trytond.pyson import If, Equal, Eval, Not, In, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, Button, StateTransition
from trytond.pool import Pool, PoolMeta

__all__ = ['CausticExcessive', 'CausticExcessiveLines', 'CausticExcessiveCreate', 'AuditCausticExcessiveLines',
           'AuditCausticExcessive',
           'ShipmentOutReturn', 'AuditCausticExcessiveCreate', 'CausticExcessiveStorage']


class CausticExcessiveStorage(ModelSQL, ModelView):
    "Caustic Excessive Storage"
    __name__ = "hrp_caustic_excessive_storage"

    shipment_internal = fields.Many2One('stock.shipment.internal', 'shipment_internal')
    type = fields.Selection([  # 类型
        ('caustic', u'报损'),
        ('excessive', u'报损(冲销)')
    ], 'Type')
    location = fields.Many2One('stock.location', 'location')
    product = fields.Many2One('product.product', 'Product')
    lot = fields.Many2One('stock.lot', 'Lot')
    quantity = fields.Integer('Quantity')  # 数量
    list_price = fields.Numeric('List Price', digits=(16, 2), readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)
    retail_package = fields.Many2One('product.uom', 'Retail Package')
    why = fields.Selection([  # 报损原因
        ('00', u'药品过期'),
        ('01', u'无外标签'),
        ('02', u'原包装破损'),
        ('03', u'科室自用'),
        ('04', u'近期药品'),
        ('05', u'长期不用'),
        ('06', u'停药'),
        ('07', u'病人退药'),
        ('08', u'工作失误'),
        ('09', u'单据错误'),
        ('10', u''),
    ], 'Why', depends=['caustic_why'])
    return_shipment = fields.Many2One('order_no', 'Return Shipment', select=True, readonly=True)  # 单号
    state = fields.Selection([
        ('assigned', u'未审核'),
        ('cancel', u'取消'),
        ('done', u'已审核')], 'State', select=True, required=True)


class CausticExcessive(ModelView):
    "Caustic Excessive"
    __name__ = "hrp_shipment_caustic_excessive"
    type = fields.Selection([  # 类型
        ('caustic', u'报损'),
        ('excessive', u'报损(冲销)')
    ], 'Type', states={
        'readonly': Bool(Eval('caustic_excessive_lines')),
    }, )
    product = fields.Function(
        fields.One2Many('product.product', None, 'Product'),
        'on_change_with_product')
    location = fields.Many2One('stock.location', 'location', states={
        'readonly': Bool(Eval('caustic_excessive_lines')),
    }, domain=[('id', 'in', Eval('locations'))], depends=['locations'])  # 仓库
    locations = fields.Function(fields.One2Many('stock.location', None, 'locations'), 'on_change_with_locations')
    retrieve_the_code = fields.Many2One('product.product', 'Retrieve The Code', domain=[  # 药品编码
        ('id', 'in', Eval('product')),
    ], depends=['product'], help='Drugs in code')
    lots = fields.Function(
        fields.One2Many('stock.lot', None, 'Lot'),
        'on_change_with_lots')
    lot = fields.Many2One('stock.lot', 'Lot', domain=[  # 批次
        ('product', '=', Eval('retrieve_the_code')),
        ('id', 'in', Eval('lots')),
    ], context={
        'locations': [Eval('location')],
    }, required=False, depends=['product', 'lots', 'location'])
    describe = fields.Char('describe', readonly=True)  # 描述
    drug_specifications = fields.Char('Drug Speic', readonly=True)  # 规格
    quantity = fields.Integer('Quantity')  # 数量
    caustic_why = fields.Selection([  # 报损原因
        ('00', u'药品过期'),
        ('01', u'无外标签'),
        ('02', u'原包装破损'),
        ('03', u'科室自用'),
        ('04', u'近期药品'),
        ('05', u'长期不用'),
        ('06', u'停药'),
        ('07', u'病人退药'),
        ('08', u'工作失误'),
        ('09', u'单据错误'),
    ], 'Caustic Why', states={
        'invisible': Not(Equal(Eval('type'), 'caustic'))
    }, depends=['type'])
    excessive_why = fields.Selection([  # 报溢有原因
        ('10', u''),
        ('08', u'工作失误')
    ], 'excessive_why', states={'invisible': Not(Equal(Eval('type'), 'excessive'))
                                }, depends=['type'])
    number = fields.Char('Number', select=True, states={
        'readonly': Bool(Eval('caustic_excessive_lines'))
    })  # 报损报溢单号
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    retail_package = fields.Many2One('product.uom', 'Retail Package',  # 单位
                                     domain=[
                                         ('category', '=', Eval('product_uom_category')),
                                     ],
                                     depends=['product_uom_category'],
                                     readonly=False, required=False)
    caustic_excessive_lines = fields.One2Many('hrp_shipment_caustic_excessive_lines', '', 'Caustic Excessive Lines')
    done = fields.Boolean('done')  # 完成

    @staticmethod
    def default_type():
        return 'caustic'

    @staticmethod
    def default_excessive_why():
        return '00'

    @fields.depends('retrieve_the_code', 'location', 'quantity', 'lot', 'type', 'retail_package')
    def on_change_quantity(self, name=None):
        if self.quantity and self.type == 'caustic':
            Uom = Pool().get('product.uom')
            if self.location == None or self.lot == None or self.type == None or self.retrieve_the_code == None:
                self.raise_user_error(u'请填写上边内容')
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([self.location.id], [self.retrieve_the_code.id],
                                                               with_childs=True, grouping=('product', 'lot'))
                if Uom.compute_qty(self.retrieve_the_code.default_uom,
                                   warehouse_quant[(self.location.id, self.retrieve_the_code.id, self.lot.id)],
                                   self.retail_package) < self.quantity:
                    message = str(Uom.compute_qty(self.retrieve_the_code.default_uom, warehouse_quant[
                        (self.location.id, self.retrieve_the_code.id, self.lot.id)],
                                                  self.retail_package)) + self.retail_package.name
                    self.raise_user_error(u'所选数量超过%s' % message)
                    self.quantity = 0

    @fields.depends('retrieve_the_code', 'location', 'quantity', 'lot', 'type', 'retail_package')
    def on_change_retail_package(self, name=None):
        Uom = Pool().get('product.uom')
        if self.quantity and self.type == '00' and self.retail_package:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            if self.location == None or self.lot == None or self.type == None or self.retrieve_the_code == None:
                self.raise_user_error(u'请填写上边内容', u'请填写上边内容')
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([self.location.id], [self.retrieve_the_code.id],
                                                               with_childs=True, grouping=('product', 'lot'))
                if Uom.compute_qty(self.retrieve_the_code.default_uom,
                                   warehouse_quant[(self.location.id, self.retrieve_the_code.id, self.lot.id)],
                                   self.retail_package) < self.quantity:
                    message = str(Uom.compute_qty(self.retrieve_the_code.default_uom,
                                                  warehouse_quant[
                                                      (self.location.id, self.retrieve_the_code.id, self.lot.id)],
                                                  self.retail_package)) + self.retrieve_the_code.default_uom.name
                    self.raise_user_error(u'所选数量超过%s' % message)
                    self.quantity = 0

    @fields.depends('retrieve_the_code')
    def on_change_with_product_uom_category(self, name=None):
        if self.retrieve_the_code:
            return self.retrieve_the_code.default_uom_category.id

    @fields.depends('type')
    def on_change_with_locations(self, name=None):
        Delivery = Pool().get('hrp_internal_delivery.test_straight')
        Location_id = Delivery.get_user_warehouse()
        Location = Pool().get('stock.location')
        locations = Location.search([('id', '=', Location_id)])
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        if self.type == 'caustic':
            if locations[0].storage_location.id == config.warehouse.storage_location.id:
                return [locations[0].freeze_location.id]
            return [locations[0].freeze_location.id, locations[0].storage_location.id]
        else:
            return [locations[0].id]

            # for i in locations:
            #     loc.append(i.id)
            #     loca.append(i.storage_location.id)
            #     loca.append(i.freeze_location.id)
            # if self.type == 'caustic':
            #     return loca
            # else:
            #     return loc

    @fields.depends('location')
    def on_change_with_product(self, name=None):
        if self.location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                ces = Product.products_by_location([self.location.id], with_childs=True)
                lists = ces.keys()
                for i in lists:
                    if ces[i] <= 0.0:
                        lists.remove(i)
                product_ids = []
                for g in lists:
                    product_ids.append(g[1])
            return product_ids

    @fields.depends('location')
    def on_change_with_lots(self, name=None):
        if self.location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            Lot = Pool().get('stock.lot')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.location.id], with_childs=True, grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value > 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('retrieve_the_code')
    def on_change_retrieve_the_code(self, name=None):
        if self.retrieve_the_code:
            pool = Pool()
            try:
                product_templates = pool.get('product.template')
                product_template = product_templates.search([
                    ("id", "=", int(self.retrieve_the_code.template))
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

    @fields.depends('done', 'type', 'location', 'retrieve_the_code', 'number ', 'lot', 'excessive_why', 'caustic_why',
                    'drug_specifications', 'describe', 'quantity', 'retail_package')
    def on_change_done(self, name=None):
        Uom = Pool().get('product.uom')
        if self.retrieve_the_code:
            try:
                #     if True:
                list = []
                dict = {}
                if self.type == 'caustic':
                    dict['caustic_why'] = self.caustic_why
                    if self.quantity:
                        Date = Pool().get('ir.date')
                        Product = Pool().get('product.product')
                        if self.location == None or self.lot == None or self.type == None or self.retrieve_the_code == None:
                            self.raise_user_error(u'请填写上边内容', u'请填写上边内容')
                        with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                            warehouse_quant = Product.products_by_location([self.location.id],
                                                                           [self.retrieve_the_code.id],
                                                                           with_childs=True,
                                                                           grouping=('product', 'lot'))
                            if Uom.compute_qty(self.retrieve_the_code.default_uom,
                                               warehouse_quant[
                                                   (self.location.id, self.retrieve_the_code.id, self.lot.id)],
                                               self.retail_package) < self.quantity:
                                message = str(Uom.compute_qty(self.retrieve_the_code.default_uom,
                                                              warehouse_quant[(
                                                                  self.location.id, self.retrieve_the_code.id,
                                                                  self.lot.id)],
                                                              self.retail_package)) + self.retrieve_the_code.default_uom.name
                                self.quantity = 0
                                raise Exception(u'所选数量超过%s' % message)
                else:
                    dict['caustic_why'] = self.excessive_why
                dict['describe'] = self.describe
                dict['retrieve_the_code'] = self.retrieve_the_code.id
                dict['product_name'] = self.retrieve_the_code.name
                dict['product_code'] = self.retrieve_the_code.code
                dict['drug_specifications'] = self.drug_specifications
                dict['quantity'] = self.quantity
                dict['retail_package'] = self.retail_package.id
                dict['describe'] = self.describe
                dict['lot'] = self.lot.id
                if self.retrieve_the_code.default_uom != self.retail_package:
                    dict['cost_price'] = Uom.compute_price(self.retrieve_the_code.default_uom,
                                                           self.retrieve_the_code.cost_price,
                                                           self.retail_package) * decimal.Decimal(str(self.quantity))
                    dict['list_price'] = Uom.compute_price(self.retrieve_the_code.default_uom,
                                                           self.retrieve_the_code.list_price,
                                                           self.retail_package) * decimal.Decimal(str(self.quantity))
                else:
                    dict['cost_price'] = self.retrieve_the_code.cost_price * decimal.Decimal(str(self.quantity))
                    dict['list_price'] = self.retrieve_the_code.list_price * decimal.Decimal(str(self.quantity))
                dict['exp_date'] = self.lot.shelf_life_expiration_date
                list.append(dict)
                self.caustic_excessive_lines = list
                self.drug_specifications = None
                self.lot = None
                self.quantity = None
                self.retrieve_the_code = None
                self.describe = None
                self.lot = None
                self.retail_package = None
                self.done = False
            except:
                self.caustic_excessive_lines = None


class CausticExcessiveLines(ModelView):
    "Caustic Excessive Lines"
    __name__ = "hrp_shipment_caustic_excessive_lines"

    product_name = fields.Char('product_name', readonly=True)
    product_code = fields.Char('product_code', readonly=True)
    retrieve_the_code = fields.Many2One('product.product', 'Retrieve The Code', domain=[  # 药品编码
        ('id', 'in', Eval('product')),
    ], depends=['product'], help='Drugs in code')
    retail_package = fields.Many2One('product.uom', 'Retail Package',  # 单位
                                     domain=[
                                         ('category', '=', Eval('product_uom_category')),
                                     ],
                                     depends=['product_uom_category'],
                                     readonly=False, required=False)
    describe = fields.Char('describe')  # 描述
    list_price = fields.Numeric('List Price', digits=(16, 2), readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)  # 规格
    quantity = fields.Integer('Quantity')  # 数量
    caustic_why = fields.Selection([  # 报损原因
        ('00', u'药品过期'),
        ('01', u'无外标签'),
        ('02', u'原包装破损'),
        ('03', u'科室自用'),
        ('04', u'近期药品'),
        ('05', u'长期不用'),
        ('06', u'停药'),
        ('07', u'病人退药'),
        ('08', u'工作失误'),
        ('09', u'单据错误'),
        ('10', u''),
    ], 'Caustic Why', depends=['caustic_why'])
    lot = fields.Many2One('stock.lot', 'Lot', domain=[  # 批次
        ('product', '=', Eval('retrieve_the_code')),
        ('id', 'in', Eval('lots')),
    ], required=False, depends=['product', 'lots'])
    exp_date = fields.Function(fields.Date('Exp Date', readonly=True), 'get_exp_date', 'set_exp_date')  # 有效日期

    def get_exp_date(self, name):
        if self.lot:
            return self.lot.shelf_life_expiration_date


class CausticExcessiveCreate(Wizard):
    "Caustic Excessive Create"
    ''' 报损 报益 管理'''
    __name__ = "hrp_shipment_caustic_excessive_Create"

    start = StateView('hrp_shipment_caustic_excessive',
                      'hrp_shipment.hrp_shipment_caustic_excessive_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_hrp_shipment_caustic_excessive_create')

    def do_create_(self, action):
        CausticExcessiveStorage = Pool().get('hrp_caustic_excessive_storage')
        ShipmentInternal = Pool().get('stock.shipment.internal')
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')
        Move = Pool().get('stock.move')
        Lot = Pool().get('stock.lot')
        OrderNo = Pool().get('order_no')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        Location = Pool().get('stock.location')
        Date = Pool().get('ir.date')
        today = str(Date.today())
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        # try:
        if True:
            if Location(data['start']['location']).type != 'warehouse':
                Location_warehouse = Location.search([('type', '=', 'warehouse'),
                                                      ('code', '=', Location(data['start']['location']).code)])
                location_parent = Location_warehouse[0].id
            else:
                location_parent = data['start']['location']
            order_no = OrderNo.search([('location', '=', location_parent),
                                       ('order_category', '=', 'caustic')],
                                      order=[["create_date", "DESC"]])

            if order_no:
                if int(order_no[0].number[2:8]) == int(time.strftime('%Y%m', time.localtime())):
                    squence = Location(location_parent).code + 'W' + time.strftime('%Y%m', time.localtime()) + str(
                        int(order_no[0].number[9:]) + 1).zfill(4)
                else:
                    squence = Location(location_parent).code + 'W' + time.strftime('%Y%m',
                                                                                   time.localtime()) + '1'.zfill(4)
            else:
                squence = Location(location_parent).code + 'W' + time.strftime('%Y%m', time.localtime()) + '1'.zfill(4)

            return_shipment = OrderNo.create([{'number': squence, 'time': today,
                                               'order_category': 'caustic',
                                               'location': location_parent}])
            message = ''
            for caustic_excessive_lines in data['start']['caustic_excessive_lines']:
                lv = {}
                lv['type'] = data['start']['type']
                lv['location'] = data['start']['location']
                lv['product'] = caustic_excessive_lines['retrieve_the_code']
                lv['lot'] = caustic_excessive_lines['lot']
                lv['quantity'] = caustic_excessive_lines['quantity']
                lv['retail_package'] = caustic_excessive_lines['retail_package']
                lv['why'] = caustic_excessive_lines['caustic_why']
                lv['state'] = 'assigned'
                lv['list_price'] = caustic_excessive_lines['list_price'].quantize(Decimal('0.00'))
                lv['cost_price'] = caustic_excessive_lines['cost_price'].quantize(Decimal('0.00'))
                if data['start']['type'] == 'caustic':
                    lvc = {}
                    lvc['company'] = 1
                    lvc['to_location'] = config.default_scrap.id
                    lvc['from_location'] = data['start']['location']
                    lvc['return_shipment'] = return_shipment[0].id
                    lvc['state'] = u'draft'
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                        pbl = Product.products_by_location([data['start']['location']],
                                                           [caustic_excessive_lines['retrieve_the_code']],
                                                           with_childs=True, grouping=('product', 'lot'))
                        forecast_quantity = pbl[(
                            data['start']['location'], caustic_excessive_lines['retrieve_the_code'],
                            caustic_excessive_lines['lot'])]
                    if Product(caustic_excessive_lines['retrieve_the_code']).default_uom != Uom(
                            caustic_excessive_lines['retail_package']):
                        unit_prices = Uom.compute_price(
                            Product(caustic_excessive_lines['retrieve_the_code']).default_uom,
                            Product(caustic_excessive_lines['retrieve_the_code']).cost_price,
                            Uom(caustic_excessive_lines['retail_package']))
                        list_prices = Uom.compute_price(
                            Product(caustic_excessive_lines['retrieve_the_code']).default_uom,
                            Product(caustic_excessive_lines['retrieve_the_code']).list_price,
                            Uom(caustic_excessive_lines['retail_package']))
                        list_price = Decimal(list_prices).quantize(Decimal('0.0000'))
                        unit_price = Decimal(unit_prices).quantize(Decimal('0.0000'))
                    else:
                        list_price = Product(caustic_excessive_lines['retrieve_the_code']).cost_price
                        unit_price = Product(caustic_excessive_lines['retrieve_the_code']).list_price
                    list = []
                    dict = {}
                    dict['origin'] = None  # each['origin']
                    dict['to_location'] = config.default_scrap.id
                    dict['actual_return'] = unit_price * decimal.Decimal(str(caustic_excessive_lines['quantity']))
                    dict['product'] = caustic_excessive_lines['retrieve_the_code']
                    dict['list_price'] = caustic_excessive_lines['list_price'].quantize(Decimal('0.00'))
                    dict['cost_price'] = caustic_excessive_lines['cost_price'].quantize(Decimal('0.00'))
                    dict['from_location'] = data['start']['location']
                    dict['invoice_lines'] = ()
                    dict['company'] = Transaction().context.get('company')
                    dict['unit_price'] = unit_price
                    dict['lot'] = caustic_excessive_lines['lot']  # 产品批次
                    dict['uom'] = caustic_excessive_lines['retail_package']  # 产品单位
                    dict['move_type'] = '802'
                    dict['quantity'] = caustic_excessive_lines['quantity']
                    list.append(dict)
                    lvc['moves'] = [['create', list]]
                    lvc['planned_date'] = today
                    Internal = ShipmentInternal.create([lvc])
                    lv['return_shipment'] = return_shipment[0].id
                    lv['shipment_internal'] = Internal[0].id
                    CausticExcessiveStorage.create([lv])
                    whether_move = Move.assign_try([Move(Internal[0].moves[0].id)], grouping=('product', 'lot'))
                    if not whether_move:
                        message += Product(caustic_excessive_lines['retrieve_the_code']).code + Product(
                            caustic_excessive_lines['retrieve_the_code']).name + u'-批次:' + Lot(
                            caustic_excessive_lines['lot']).number + u'当前数量为,' + str(forecast_quantity) + Uom(
                            caustic_excessive_lines['retail_package']).name + u'请删除该行项目后重新输入\n'
                        continue
                    ShipmentInternal.wait(Internal)
                    ShipmentInternal.assign_try(Internal)
                    # ShipmentInternal.done(Internal)
                else:  # data['start']['type'] == 'excessive':
                    lv['return_shipment'] = return_shipment[0].id
                    CausticExcessiveStorage.create([lv])
                    # except:
                    #     self.raise_user_error(u'请填写主要内容之后在创建')
            if message:
                self.raise_user_error(message)
        return action, {}


class ShipmentOutReturn:
    "Customer Return Shipment"
    __metaclass__ = PoolMeta
    __name__ = 'stock.shipment.out.return'
    _rec_name = 'number'
    return_shipment = fields.Many2One('order_no', 'Return Shipment', select=True, readonly=True)


class AuditCausticExcessiveLines(ModelView):
    "Audit Caustic Excessive Lines"
    __name__ = "hrp_shipment_Audit_caustic_excessive_lines"

    shipment_internal = fields.Many2One('stock.shipment.internal', 'shipment_internal')
    audit_id = fields.Integer('audit_id', readonly=True)
    lines = fields.Integer('Lines', readonly=True)
    product_name = fields.Char('product_name', readonly=True)
    product_code = fields.Char('product_code', readonly=True)
    retrieve_the_code = fields.Many2One('product.product', 'Retrieve The Code', domain=[  # 药品编码
        ('id', 'in', Eval('product')),
    ], depends=['product'], help='Drugs in code', readonly=True)
    retail_package = fields.Many2One('product.uom', 'Retail Package',  # 单位
                                     domain=[
                                         ('category', '=', Eval('product_uom_category')),
                                     ],
                                     depends=['product_uom_category'],
                                     readonly=True, required=False)
    describe = fields.Char('describe', readonly=True)  # 描述
    list_price = fields.Numeric('List Price', digits=(16, 2), readonly=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)  # 规格
    quantity = fields.Integer('Quantity', readonly=True)  # 数量

    why = fields.Selection([  # 报损原因
        ('00', u'药品过期'),
        ('01', u'无外标签'),
        ('02', u'原包装破损'),
        ('03', u'科室自用'),
        ('04', u'近期药品'),
        ('05', u'长期不用'),
        ('06', u'停药'),
        ('07', u'病人退药'),
        ('08', u'工作失误'),
        ('09', u'单据错误'),
        ('10', u''),
    ], 'Why', depends=['caustic_why'], readonly=True)

    lot = fields.Many2One('stock.lot', 'Lot', domain=[  # 批次
        ('product', '=', Eval('retrieve_the_code')),
        ('id', 'in', Eval('lots')),
    ], required=False, readonly=True, depends=['product', 'lots'])
    exp_date = fields.Date('Exp Date', readonly=True)  # 有效日期
    state = fields.Selection([
        ('assigned', u'未审核'),
        ('cancel', u'取消'),
        ('done', u'已审核')], 'State', select=True, required=True)


class AuditCausticExcessive(ModelView):
    "Audit Caustic Excessive Lines"
    __name__ = "hrp_shipment_Audit_caustic_excessive"

    type = fields.Selection([  # 类型
        ('caustic', u'报损'),
        ('excessive', u'报损(冲销)')
    ], 'Type', states={
        'readonly': Bool(Eval('caustic_excessive_lines')),
    }, required=True)

    state = fields.Selection([
        ('assigned', u'未审核'),
        ('done', u'已审核')], 'State', select=True, required=True)

    location = fields.Many2One('stock.location', 'location', required=True, states={
        'readonly': Bool(Eval('caustic_excessive_lines')),
    }, domain=[('id', 'in', Eval('locations'))], depends=['locations'])  # 仓库
    locations = fields.Function(fields.One2Many('stock.location', None, 'locations'), 'on_change_with_locations')
    order_no_with = fields.Function(fields.One2Many('order_no', None, 'order_no_with'), 'on_change_with_order_no_with')
    order_no = fields.Many2One('order_no', 'Order', required=True, select=True,
                               domain=[('id', 'in', Eval('order_no_with'))], depends=['order_no_with'], )
    audit_caustic_excessive_lines = fields.One2Many('hrp_shipment_Audit_caustic_excessive_lines', '',
                                                    'Audit Caustic Excessive Lines')

    @staticmethod
    def default_state():
        return 'assigned'

    @fields.depends('state', 'type', 'location')
    def on_change_with_order_no_with(self, name=None):
        CausticExcessiveStorage = Pool().get('hrp_caustic_excessive_storage')
        if self.state and self.type and self.location:
            if self.type == 'caustic':
                Location = Pool().get('stock.location')
                location = Location.search([('id', '=', self.location.id)])
                loca = [location[0].freeze_location, location[0].storage_location]
                search = [('state', '=', self.state), ('type', '=', self.type), ('location', 'in', loca)]
            else:
                search = [('state', '=', self.state), ('type', '=', self.type), ('location', '=', self.location)]
            caustic_excessive_storag = CausticExcessiveStorage.search([search])
            order_no_id = []
            for i in caustic_excessive_storag:
                order_no_id.append(i.return_shipment.id)
            return order_no_id

    @fields.depends('type')
    def on_change_with_locations(self, name=None):
        Location = Pool().get('stock.location')
        locations = Location.search([('type', '=', 'warehouse')])
        loc = []
        for i in locations:
            loc.append(i.id)
        return loc

    @fields.depends('type', 'order_no', 'state', 'audit_caustic_excessive_lines', 'location')
    def on_change_order_no(self, name=None):
        if self.type and self.state and self.location:
            if self.type == 'caustic':
                Location = Pool().get('stock.location')
                location = Location.search([('id', '=', self.location.id)])
                loca = [location[0].freeze_location, location[0].storage_location]
                search = [('state', '=', self.state), ('type', '=', self.type),
                          ('return_shipment', '=', self.order_no), ('location', 'in', loca)]
            else:
                search = [('state', '=', self.state), ('type', '=', self.type),
                          ('return_shipment', '=', self.order_no), ('location', '=', self.location)]
            CausticExcessiveStorage = Pool().get('hrp_caustic_excessive_storage')
            caustic_excessive_storag = CausticExcessiveStorage.search(search)
            lines = []
            if caustic_excessive_storag:
                line = 1
                for each in caustic_excessive_storag:
                    dict = {}
                    try:
                        dict['describe'] = each.product.template.attach
                    except:
                        pass
                    dict['audit_id'] = each.id
                    dict['shipment_internal'] = each.shipment_internal
                    dict['lines'] = line
                    dict['product_code'] = each.product.code
                    dict['product_name'] = each.product.template.name
                    dict['drug_specifications'] = each.product.template.drug_specifications
                    dict['quantity'] = each.quantity
                    dict['list_price'] = each.list_price
                    dict['cost_price'] = each.cost_price
                    dict['retail_package'] = each.retail_package
                    dict['lot'] = each.lot
                    dict['state'] = each.state
                    dict['why'] = each.why
                    dict['exp_date'] = each.lot.shelf_life_expiration_date
                    lines.append(dict)
                    line += 1
            self.audit_caustic_excessive_lines = lines


class AuditCausticExcessiveCreate(Wizard):
    "Audit Caustic Excessive Create"
    __name__ = "hrp_shipment_audit_caustic_excessive_create"

    start = StateView('hrp_shipment_Audit_caustic_excessive',
                      'hrp_shipment.hrp_shipment_Audit_caustic_excessive_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_hrp_shipment_audit_caustic_excessive_create')

    def do_create_(self, action):
        CausticExcessiveStorage = Pool().get('hrp_caustic_excessive_storage')
        ShipmentInternal = Pool().get('stock.shipment.internal')
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')
        Move = Pool().get('stock.move')
        Lot = Pool().get('stock.lot')
        ShipmentOutReturn = Pool().get('stock.shipment.out.return')
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
            messages = ''
            for audit_caustic_excessive_lines in data['start']['audit_caustic_excessive_lines']:
                caustic_excessive_storag = CausticExcessiveStorage.search([
                    ('id', '=', audit_caustic_excessive_lines['audit_id'])])
                CausticExcessiveStorage.write(caustic_excessive_storag,
                                              {'state': audit_caustic_excessive_lines['state']})
                if audit_caustic_excessive_lines['state'] == 'done':

                    product_template = Product.search([
                        ("id", "=", caustic_excessive_storag[0].product.id)])
                    if audit_caustic_excessive_lines != None:
                        if caustic_excessive_storag[0].product.default_uom != Uom(
                                audit_caustic_excessive_lines['retail_package']):
                            unit_price = Uom.compute_price(
                                caustic_excessive_storag[0].product.default_uom,
                                caustic_excessive_storag[0].product.cost_price,
                                Uom(audit_caustic_excessive_lines['retail_package']))
                            list_price = Uom.compute_price(
                                caustic_excessive_storag[0].product.default_uom,
                                caustic_excessive_storag[0].product.list_price,
                                Uom(audit_caustic_excessive_lines['retail_package']))
                        else:
                            unit_price = caustic_excessive_storag[0].product.cost_price,
                            list_price = caustic_excessive_storag[0].product.list_price,
                        if data['start']['type'] == 'excessive':
                            incoming_moves = [
                                [
                                    u'create',
                                    [
                                        {
                                            u'comment': u'',
                                            u'outgoing_audit': u'00',
                                            u'product': caustic_excessive_storag[0].product.id,
                                            u'to_location': caustic_excessive_storag[0].location.input_location.id,
                                            u'from_location': config.caustic_excessive.customer_location.id,
                                            u'invoice_lines': [],
                                            u'cost_price': unit_price,
                                            u'list_price:': list_price,
                                            u'starts': u'05',
                                            u'actual_return': unit_price * decimal.Decimal(
                                                str(audit_caustic_excessive_lines['quantity'])),
                                            u'move_type': '801',
                                            u'company': Transaction().context.get('company'),
                                            u'unit_price': unit_price,
                                            u'currency': currency.id,
                                            u'reason': '00',
                                            u'lot': audit_caustic_excessive_lines['lot'],
                                            u'planned_date': today,
                                            u'uom': audit_caustic_excessive_lines['retail_package'],
                                            u'origin': u'stock.inventory.line,-1',
                                            u'quantity': audit_caustic_excessive_lines['quantity'],
                                            u'real_number': None,
                                        }
                                    ]
                                ]
                            ]
                            lv = [
                                {
                                    u'customer': config.caustic_excessive.id,
                                    u'delivery_address': config.caustic_excessive.address_get('delivery').id,
                                    u'reference': u'',
                                    u'planned_date': today,
                                    u'company': Transaction().context.get('company'),
                                    u'incoming_moves': incoming_moves,
                                    u'warehouse': data['start']['location'],
                                    u'effective_date': today,
                                    u'inventory_moves': [],
                                }
                            ]
                            shipmeng_out_returns = ShipmentOutReturn.create(lv)
                            shipmeng_out_return = ShipmentOutReturn.search([('id', '=', shipmeng_out_returns[0].id)])
                            ShipmentOutReturn.receive(shipmeng_out_return)
                            ShipmentOutReturn.done(shipmeng_out_return)
                        else:
                            Internal = ShipmentInternal.search(
                                [('id', '=', audit_caustic_excessive_lines['shipment_internal']),
                                 ('state', '!=', 'done')])
                            if Internal:
                                ShipmentInternal.wait(Internal)
                                whether_move = Move.assign_try([Move(Internal[0].moves[0].id)],
                                                               grouping=('product', 'lot'))
                                if not whether_move:
                                    context = ({'stock_date_end': Date.today(), 'forecast': True})
                                    with Transaction().set_context(context=context):
                                        pbl = Product.products_by_location(
                                            [caustic_excessive_storag[0].location.input_location.id],
                                            [caustic_excessive_storag[0].product.id], with_childs=True,
                                            grouping=('product', 'lot'))
                                        forecast_quantity = pbl[
                                            (caustic_excessive_storag[0].location.input_location.id,
                                             caustic_excessive_storag[0].product.id,
                                             audit_caustic_excessive_lines['lot'])]
                                    message += Internal[0].moves[0].product.code + Internal[0].moves[
                                        0].product.name + u'-批次:' + Lot(
                                        Internal[0].moves[0].lot).number + u'当前数量为' + str(forecast_quantity) + Uom(
                                        audit_caustic_excessive_lines['retail_package']).name + u',请删除该行项目后重新输入\n'
                                    continue
                                ShipmentInternal.assign_try(Internal)
                                ShipmentInternal.done(Internal)
                            else:
                                messages = u'该单号已被处理,请退出后重新查询。'
                if audit_caustic_excessive_lines['state'] == 'cancel':
                    Internal = ShipmentInternal.search(
                        [('id', '=', audit_caustic_excessive_lines['shipment_internal'])])
                    ShipmentInternal.cancel(Internal)
            if message:
                self.raise_user_error(message)
            if messages:
                self.raise_user_error(messages)
        return action, {}
