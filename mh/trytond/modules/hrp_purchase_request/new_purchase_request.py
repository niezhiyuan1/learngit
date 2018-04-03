# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import decimal

from trytond.model import ModelView, fields, Workflow
from trytond.model import ModelView
from trytond.modules.stock import Location, Product
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Eval, Bool, PYSONEncoder, Id


__all_ =['NewCreatePurchaseRequestStart','NewCreatePurchaseRequest','Purchase','OrderPoint']

STATES = {
    'readonly': Eval('state') != 'draft',
    }
DEPENDS = ['state']

class Purchase:
    __name__ = 'purchase.purchase'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(Purchase, cls).__setup__()
        cls._order = [
            ('purchase_date', 'DESC'),
            ('id', 'DESC'),
        ]
        cls._error_messages.update({
            'warehouse_required': ('A warehouse must be defined for '
                                   'quotation of purchase "%s".'),
            'missing_account_payable': ('Missing "Account Payable" on '
                                        'party "%s".'),
            'delete_cancel': ('Purchase "%s" must be cancelled before '
                              'deletion.'),
        })
        cls._transitions |= set((
            ('draft', 'quotation'),
            ('quotation', 'confirmed'),
            ('confirmed', 'processing'),
            ('processing', 'processing'),
            ('processing', 'done'),
            ('done', 'processing'),
            ('draft', 'cancel'),
            ('quotation', 'cancel'),
            ('quotation', 'draft'),
            ('cancel', 'draft'),
        ))
        cls._buttons.update({
            'cancel': {
                'invisible': ~Eval('state').in_(['draft', 'quotation']),
            },
            'draft': {
                'invisible': ~Eval('state').in_(['cancel', 'quotation']),
                'icon': If(Eval('state') == 'cancel', 'tryton-clear',
                           'tryton-go-previous'),
            },
            'quote': {
                'pre_validate': [
                    ('purchase_date', '!=', None),
                    ('payment_term', '!=', None),
                    ('invoice_address', '!=', None),
                ],
                'invisible': Eval('state') != 'draft',
                'readonly': ~Eval('lines', []),
            },
            'confirm': {
                'invisible': Eval('state') != 'quotation',
            },
            'process': {
                'invisible': Eval('state') != 'confirmed',
            },
            'handle_invoice_exception': {
                'invisible': ((Eval('invoice_state') != 'exception')
                              | (Eval('state') == 'cancel')),
                'readonly': ~Eval('groups', []).contains(
                    Id('purchase', 'group_purchase')),
            },
            'handle_shipment_exception': {
                'invisible': ((Eval('shipment_state') != 'exception')
                              | (Eval('state') == 'cancel')),
                'readonly': ~Eval('groups', []).contains(
                    Id('purchase', 'group_purchase')),
            },
        })
        # The states where amounts are cached
        cls._states_cached = ['confirmed', 'done', 'cancel']

    @classmethod
    @ModelView.button
    @Workflow.transition('quotation')
    def quote(cls, purchases):
        Internal = Pool().get('stock.shipment.internal')
        Move = Pool().get('stock.move')
        for purchase in purchases:
            purchase.check_for_quotation()
        cls.set_number(purchases)
        PurchaseBills = Pool().get('purchase_bills')
        for purchase in purchases:
            bills = PurchaseBills.search([('order_code','=',purchase.number)])
            if not bills:
                dict_head = {}
                dict_head['party'] = purchase.party.id
                dict_head['purchase_create_time'] = purchase.purchase_date
                dict_head['order_code'] = purchase.number
                dict_head['served_to'] = purchase.delivery_place
                dict_head['state'] = 'draft'
                dict_head['source'] = '00'
                for line in purchase.lines:
                    dict_line = {}
                    try:
                        dict_line['internal_orders'] = line.internal_order
                        internal = Internal.search([('number', '=', str(line.internal_order))])
                        for move in internal[0].moves:
                            if move.product.id == line.product.id and move.change_start == True:
                                Move.write([move],{'change_start': False,'purchase_order': str(purchase.number)})
                    except:
                        pass
                    dict_line['line_code'] = line.sequence
                    dict_line['product'] = line.product.id
                    dict_line['categories'] = line.product.categories[0].id
                    dict_line['purchase_quantity'] = line.quantity
                    dict_line['invoice_amount'] = line.product.cost_price * decimal.Decimal(str(line.quantity))
                    dict_line['retail_amount'] = round(line.product.list_price * decimal.Decimal(str(line.quantity)))
                    dicts = dict(dict_head,**dict_line)
                    PurchaseBills.create([dicts])

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, purchases):
        cls.store_cache(purchases)
        for purchase in purchases:
            PurchaseBills = Pool().get('purchase_bills')
            bills = PurchaseBills.search([('order_code', '=', purchase.number)])
            PurchaseBills.delete(bills)





class NewCreatePurchaseRequestStart(ModelView):
    'NewCreate Purchase Request'
    __name__ = 'hrp_purchase_request.request.create.start'

    product = fields.Many2One('product.product', 'Product',
        ondelete='RESTRICT', domain=[('salable', '=', True)],

        context={
            'locations': If(Bool(Eval('_parent_sale', {}).get('warehouse')),
                [Eval('_parent_sale', {}).get('warehouse', 0)], []),
            'stock_date_end': Eval('_parent_sale', {}).get('sale_date'),
            'stock_skip_warehouse': True,
            }, depends=['type'])
    quantity = fields.Float('Quantity', readonly=False,required=True)
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    uom = fields.Many2One('product.uom', 'UOM',domain=[
            ('category', '=', Eval('product_uom_category')),
            ],
        depends=['product_uom_category'],
        readonly=False,required=True)
    stock_level = fields.Float('Stock at Supply Date', readonly=True,
        digits=(16, Eval('default_uom_digits', 2)),
        depends=['default_uom_digits'])

    warehouse = fields.Many2One(
        'stock.location', "Warehouse",
        states={
            'required': Eval('warehouse_required', False),
            },
        domain=[('type', '=', 'warehouse')], depends=['warehouse_required'],
        readonly=False,required=True)
    a_charge = fields.Integer('A_charge',select=True,readonly=True)
    attach = fields.Char('Attach',select=True,readonly=True)
    retrieve_the_code = fields.Char('Retrieve_the_code',select=True,readonly=True)
    drug_specifications = fields.Char('Drug_specifications',select=True,readonly=True)
    is_direct_sending = fields.Boolean('Is_direct_sending',select=True)

    @staticmethod
    def default_warehouse():
        purchase_configurations = Pool().get('purchase.configuration')
        purchase_configuration = purchase_configurations.search([])
        purchase_configuration = int(purchase_configuration[0].warehouse)
        if purchase_configuration == None:
            raise ValueError('Please fill in the product configuration')
        else:
            return purchase_configuration

    @fields.depends('warehouse','product')
    def on_change_product(self):
        pool = Pool()
        Date_ = pool.get('ir.date')
        Product = pool.get('product.product')
        if self.warehouse and self.product:
            with Transaction().set_context(stock_date_end=Date_.today()):
                quantities = Product.products_by_location([self.warehouse.id],[self.product.id], with_childs=True)
            if quantities.values():
                quantity = [v for v in quantities.values()][0]
                self.stock_level = quantity
        if self.product:
            products = Product.search([
                ('id','=',self.product.id)
                ])
            if products:
                self.drug_specifications = products[0].drug_specifications
                self.retrieve_the_code = products[0].retrieve_the_code
                self.attach = products[0].attach
                self.a_charge = products[0].a_charge
                self.is_direct_sending = products[0].is_direct_sending
                self.uom = products[0].default_uom

    @fields.depends('warehouse','product')
    def on_change_warehouse(self):
        if self.warehouse and self.product:
            pool = Pool()
            Date_ = pool.get('ir.date')
            Product = pool.get('product.product')
            with Transaction().set_context(stock_date_end=Date_.today()):
                quantities = Product.products_by_location([self.warehouse.id],[self.product.id], with_childs=True)
            if quantities.values():
                quantity = [v for v in quantities.values()][0]
                self.stock_level = quantity
    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

class NewCreatePurchaseRequest(Wizard):
    'Create Purchase Requests'
    __name__ = 'hrp_purchase_request.request.create'
    start = StateView('hrp_purchase_request.request.create.start',
        'hrp_purchase_request.new_purchase_request_create_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('purchase_request.act_purchase_request_form')

    def do_create_(self, action):
        pool = Pool()
        party_partysd = pool.get("purchase.request")
        Date = Pool().get('ir.date')
        today = str(Date.today())
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        lv = {}
        lv['product'] = data['start']['product']
        lv['computed_uom'] = data['start']['uom']
        lv['uom'] = data['start']['uom']
        lv['computed_quantity'] = data['start']['quantity']
        lv['quantity'] = data['start']['quantity']
        lv['warehouse'] = data['start']['warehouse']
        lv['company'] = Transaction().context['company']
        lv['purchase_date'] = today
        lv['origin'] = 'stock.order_point,'+ '-3'
        lv['party'] = None
        lv['purchase_line'] = None
        lv['supply_date'] = None
        lv['is_direct_sending'] = data['start']['is_direct_sending']
        lv['stock_level'] = data['start']['stock_level']
        party_partysd.create([lv])
        return  action,{}



