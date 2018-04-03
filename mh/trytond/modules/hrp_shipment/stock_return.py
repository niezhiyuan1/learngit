# coding:utf-8
import decimal
import operator
from trytond.model import ModelView, fields, Workflow, ModelSQL
from trytond.pyson import If, Equal, Eval, Not, In, Bool
from trytond.wizard import Wizard, StateView, StateAction, Button, StateTransition
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['OrderNo', 'StockReturn', 'StockReturnLines', 'ShipmentInReturn', 'CreateStockReturn']


class ShipmentInReturn:
    "Supplier Return Shipment"
    __metaclass__ = PoolMeta
    __name__ = 'stock.shipment.in.return'
    _rec_name = 'number'
    order_no = fields.Many2One('order_no', 'Order', readonly=True)
    categories = fields.Many2One('product.category', 'Categories', select=True, required=False, readonly=True)
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

    @staticmethod
    def default_cause():
        return '00'


class OrderNo(ModelView, ModelSQL):
    "OrderNo"
    __name__ = "order_no"
    number = fields.Char('Number', select=True, )
    time = fields.Date('Time', select=True)
    location = fields.Many2One('stock.location', 'location', select=True)
    order_category = fields.Selection([
        ('outbound', u'出库'),
        ('purchase', u'采购'),
        ('return', u'采退'),
        ('902', u'药库特殊出库'),
        ('sale_return', u'消耗'),
        ('sale_purchase', u'退药'),
        ('caustic', u'报损'),
        ('excessive', u'报溢')
    ], 'order_category', required=True)

    @classmethod
    def __setup__(cls):
        super(OrderNo, cls).__setup__()
        cls._order[0] = ('id', 'DESC')

    def get_rec_name(self, name):
        return self.number


class StockReturn(ModelView):
    "Stock Return"
    __name__ = "stock_return"
    _rec_name = 'stock_return'

    order_category = fields.Selection([
        ('purchase', u'采购'),
        ('return', u'采退')
    ], 'order_category', states={
        'readonly': Bool(Eval('stock_return_lines'))}, required=True)
    categories = fields.Many2One('product.category', 'Categories', select=True, required=True,
                                 states={'readonly': Bool(Eval('stock_return_lines'))})
    order_no_with = fields.Function(fields.One2Many('order_no', None, 'order_no_with'), 'on_change_with_order_no_with')
    order_no = fields.Many2One('order_no', 'Order', required=True, select=True,
                               domain=[('id', 'in', Eval('order_no_with'))], depends=['order_no_with'])
    stock_return_lines = fields.One2Many('stock_return_lines', '', 'HrpShipmentReturnLines',
                                         states={'readonly': Equal(Eval('state'), 'done')})
    state = fields.Selection([
        ('assigned', u'未完成'),
        ('done', u'已完成')], 'State', select=True, required=True)
    confirm = fields.Boolean('confirm', states={'readonly': False, })

    @staticmethod
    def default_state():
        return 'assigned'

    @staticmethod
    def default_order_category():
        return 'purchase'

    @fields.depends('categories', 'state', 'order_category')
    def on_change_with_order_no_with(self, name=None):
        if self.categories and self.state and self.order_category == 'return':
            ShipmentInReturn = Pool().get('stock.shipment.in.return')
            state = self.state
            if self.state == 'assigned':
                state = 'waiting'
            shipmentinreturn = ShipmentInReturn.search([
                ('categories', '=', self.categories.id),
                ('state', '=', state)
            ])
            order_no_id = []
            for i in shipmentinreturn:
                order_no_id.append(i.order_no.id)
            return order_no_id
        if self.categories and self.state and self.order_category == 'purchase':
            PurchaseBills = Pool().get('purchase_bills')
            bills = PurchaseBills.search([('state', '=', self.state), ('categories', '=', self.categories)])
            order_no_id = []
            for i in bills:
                order_no_id.append(i.return_shipment.id)
            return order_no_id

    @fields.depends('categories', 'order_no', 'state', 'stock_return_lines', 'confirm', 'order_category')
    def on_change_order_no(self, name=None):
        if self.order_category == 'return' and self.state:
            ShipmentInReturn = Pool().get('stock.shipment.in.return')
            state = self.state
            if self.state == 'assigned':
                state = 'waiting'
            shipmentinreturn = ShipmentInReturn.search(
                [('categories', '=', self.categories),
                 ('state', '=', state),
                 ('order_no', '=', self.order_no),
                 ])
            lines = []
            line = 1
            for each in shipmentinreturn:
                dict = {}
                dict['return_id'] = each.id
                dict['line'] = line
                dict['code'] = each.moves[0].product.code
                try:
                    dict['note'] = each.moves[0].product.template.attach
                except:
                    pass
                dict['lot'] = each.moves[0].lot.id
                dict['shelf_life_expiration_date'] = each.moves[0].lot.shelf_life_expiration_date
                dict['product_name'] = each.moves[0].product.template.name
                dict['drug_specifications'] = each.moves[0].product.template.drug_specifications
                dict['quantity'] = each.moves[0].quantity
                lines.append(dict)
                line += 1
            self.stock_return_lines = lines
        if self.order_category == 'purchase' and self.state:
            PurchaseBills = Pool().get('purchase_bills')
            bills = PurchaseBills.search([('state', '=', self.state),
                                          ('categories', '=', self.categories),
                                          ('return_shipment', '=', self.order_no)])
            lines = []
            line = 1
            for each in bills:
                dict = {}
                dict['purchase_id'] = each.id
                dict['line'] = line
                dict['code'] = each.product.code
                try:
                    dict['note'] = each.product.template.attach
                except:
                    pass
                dict['lot'] = each.lot.id
                dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                dict['product_name'] = each.product.template.name
                dict['drug_specifications'] = each.product.template.drug_specifications
                dict['quantity'] = each.shipment_quantity
                lines.append(dict)
                line += 1
            self.stock_return_lines = lines


class StockReturnLines(ModelView):
    "Stock Return Lines"
    __name__ = "stock_return_lines"
    _rec_name = 'stock_return_lines'

    return_id = fields.Many2One('stock.shipment.in.return', 'Return ID')
    purchase_id = fields.Many2One('purchase_bills', 'Purchase ID')
    line = fields.Integer('line', readonly=True)
    order = fields.Many2One('order_no', 'Order', select=True)
    code = fields.Char('code', readonly=True)
    product_name = fields.Char('Product_name', readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    note = fields.Char('Note', select=True, readonly=True)
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    ensure = fields.Boolean('ensure', states={'readonly': False})


class CreateStockReturn(Wizard):
    'Create Stock Return'
    __name__ = 'create_stock_return'
    start = StateView('stock_return',
                      'hrp_shipment.stock_return_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_shipment.act_create_stock_return')

    def do_create_(self, action):
        Product = Pool().get('product.product')
        ProductQuantity = Pool().get('product_quantity')
        Purchase = Pool().get('purchase.purchase')
        Company = Pool().get('company.company')
        Date = Pool().get('ir.date')
        Move = Pool().get('stock.move')
        Lot = Pool().get('stock.lot')
        today = str(Date.today())
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        company = Company.search([('id', '=', Transaction().context['company'])])
        currency = company[0].currency
        Invoice = Pool().get('account.invoice')
        ShipmentIn = Pool().get('stock.shipment.in')
        PurchaseBills = Pool().get('purchase_bills')
        ShipmentInReturn = Pool().get('stock.shipment.in.return')
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        message = ''
        for each in data['start']['stock_return_lines']:
            if each['ensure'] == True and data['start']['order_category'] == 'return':
                shipmentinreturn = ShipmentInReturn.search(
                    [('id', '=', each['return_id']),
                     ('state', '!=', 'done')])
                if not shipmentinreturn:
                    message = u'该单号已被处理,请退出后重新查询。'
                    continue
                whether_move = Move.assign_try([Move(shipmentinreturn[0].moves[0].id)], grouping=('product', 'lot'))
                if not whether_move:
                    message += shipmentinreturn[0].moves[0].product.code + shipmentinreturn[0].moves[
                        0].product.name + u'-批次:' + Lot(
                        shipmentinreturn[0].moves[0].lot).number + u'实际数量有变,请删除该行项目后重新输入\n'
                    continue
                ShipmentInReturn.assign(shipmentinreturn)
                ShipmentInReturn.done(shipmentinreturn)
            if each['ensure'] == True and data['start']['order_category'] == 'purchase':
                purchase_bills = PurchaseBills.search([('id', '=', each['purchase_id'])])
                purchase = Purchase.search(
                    [('number', '=', purchase_bills[0].order_code)])  # ,('state', '!=', 'processing')
                if not purchase:
                    message = u'该单号已被处理,请退出后重新查询。'
                    continue
                PurchaseBills.write(purchase_bills, {'state': 'done'})
                Purchase.quote(purchase)
                Purchase.confirm(purchase)
                Purchase.process(purchase)
                moves = Move.search([
                    ('product', '=', purchase_bills[0].product.id),
                    ('purchase', '=', purchase_bills[0].order_code),
                    ('state', '=', 'draft')
                ])
                Move.write(moves, {'outgoing_audit': '02', 'lot': purchase_bills[0].lot.id,
                                   'quantity': purchase_bills[0].shipment_quantity, 'move_type': '101'})
                lv = {}
                if moves != []:
                    lv['incoming_moves'] = [['add', [moves[0].id]]]
                lv['reference'] = ''
                lv['planned_date'] = today
                lv['return_shipment'] = purchase_bills[0].return_shipment
                lv['company'] = Transaction().context.get('company')
                lv['effective_date'] = None
                lv['cause'] = '00'
                lv['warehouse'] = config.warehouse.id
                lv['supplier'] = purchase_bills[0].party.id
                lv['inventory_moves'] = []
                shipments = ShipmentIn.create([lv])
                shipment = ShipmentIn.search([('id', '=', shipments[0].id)])
                ShipmentIn.receive(shipment)
                ShipmentIn.done(shipment)
                invoices = Invoice.search([
                    ('state', '=', 'draft'),
                    ('id', 'in', [ids.id for ids in [i for i in [k.invoices for k in purchase]][0]])
                ])
                Invoice.write(invoices, {'invoice_date': purchase_bills[0].purchase_create_time,
                                         'reference': purchase_bills[0].invoice_code,
                                         'description': purchase_bills[0].return_shipment.number,
                                         'amount': purchase_bills[0].amount_of_real_pay})
                Invoice.validate_invoice(invoices)
                Invoice.validate_invoice(invoices)

                product_quantities = ProductQuantity.search([('product', '=', purchase_bills[0].product.id)],
                                                            order=[["sequence", "ASC"]])
                move = {
                    u'comment': u'',
                    u'outgoing_audit': u'00',
                    u'product': purchase_bills[0].product.id,
                    u'from_location': config.warehouse.storage_location.id,
                    u'invoice_lines': [],
                    u'starts': u'05',
                    u'move_type': '000',
                    u'company': Transaction().context.get('company'),
                    u'unit_price': purchase_bills[0].product.cost_price,
                    u'currency': currency.id,
                    u'reason': '00',
                    u'lot': purchase_bills[0].lot.id,
                    u'planned_date': today,
                    u'uom': purchase_bills[0].product.default_uom.id,
                    u'origin': None,  # u'sale.line,-1',
                }
                move_quantity = purchase_bills[0].shipment_quantity
                for product_quantity in product_quantities:
                    with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([product_quantity.location.id],
                                                                       [purchase_bills[0].product.id], with_childs=True)
                        move['to_location'] = product_quantity.location.id
                        warehouse_quantity = warehouse_quant[
                            (product_quantity.location.id, purchase_bills[0].product.id)]
                        if product_quantity.quantity - warehouse_quantity >= move_quantity:
                            move['quantity'] = move_quantity
                            if move['quantity'] < 0:
                                self.raise_user_error(u'当前库存已超过最大库存！')
                            moves = Move.create([move])
                            Move.do(moves)
                            break
                        else:
                            move['quantity'] = product_quantity.quantity - warehouse_quantity
                            if move['quantity'] < 0:
                                self.raise_user_error(u'当前库存已超过最大库存！')
                            move_quantity = move_quantity + warehouse_quantity - product_quantity.quantity
                            moves = Move.create([move])
                            Move.do(moves)
        if message:
            self.raise_user_error(message)
        return action, {}




        ######################################
