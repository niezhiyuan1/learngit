# coding:utf-8
import time

from trytond.model import ModelView, fields, Workflow, ModelSQL
from trytond.model import ModelView
from trytond.modules.stock import Location, Product
from trytond.wizard import Wizard, StateView, StateAction, Button, StateTransition
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Eval, Bool, PYSONEncoder, Id

__all__ = ['CreatePurchaseMrpStart', 'CreatePurchaseMrp', 'PurchaseMrpLines', 'CreatePurchaseAskParty',
           'CreatePurchase', 'Lot']

STATES = {
    'readonly': ~Eval('is_create', True),
}

price_digits = (16, 2)


class PurchaseMrpLines(ModelSQL, ModelView):
    "Purchase Mrp Lines"
    __name__ = "hrp_purchase_mrp.purchase_mrp_lines"
    name = fields.Function(fields.Char('name', readonly=True, select=True), 'get_name')
    product = fields.Many2One('product.product', 'Product', required=True, select=True, readonly=True,
                              domain=[('purchasable', '=', True)])
    party = fields.Many2One('party.party', 'Party', states=STATES, readonly=True, select=False)
    quantity = fields.Float('Quantity', required=False, readonly=False, select=False,
                            digits=(16, Eval('uom_digits', 0)), depends=['uom_digits'], states=STATES, )
    advice_quantity = fields.Float('Advice_quantity', required=False, readonly=True, select=False,
                                   digits=(16, Eval('uom_digits', 2)), depends=['uom_digits'], states=STATES, )
    uom = fields.Many2One('product.uom', 'UOM', domain=[
        ('category', '=', Eval('product_uom_category')),
    ], required=False, select=False, readonly=True, depends=['product_uom_category', ])
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')

    purchase_date = fields.Date('Best Purchase Date', readonly=True, select=False, )
    stock_level = fields.Float('Stock at Supply Date', readonly=True, select=False,
                               digits=(16, Eval('default_uom_digits', 2)),
                               depends=['default_uom_digits'])
    code = fields.Function(fields.Char('Code', select=True, readonly=True), 'get_code')
    outpatient_7days = fields.Float('Outpatient_7days', readonly=True, digits=price_digits, select=False)
    hospitalized_7days = fields.Float('Hospitalized_7days', readonly=True, digits=price_digits, select=False)
    outpatient_stock = fields.Float('Outpatient_stock', readonly=True, digits=price_digits, select=False)
    hospitalized_stock = fields.Float('Hospitalized_stock', readonly=True, digits=price_digits, select=False)
    retrieve_the_code = fields.Char('Retrieve_the_code', select=True, readonly=True)
    drug_specifications = fields.Function(fields.Char('Drug_specifications', select=False, readonly=True),
                                          'get_drug_specifications')
    attach = fields.Function(fields.Char('Attach', select=False, readonly=True), 'get_attach')
    a_charge = fields.Function(fields.Integer('A_charge', select=False, readonly=True), 'get_a_charge')
    interim = fields.Function(fields.Selection([
        ('1', u''),
        ('2', u'是')], 'interim', select=False, readonly=True), 'get_interim')
    manufacturers_describtion = fields.Function(fields.Char('manufacturers_describtion', select=True, readonly=True),
                                                'get_manufacturers_describtion')
    is_create = fields.Boolean('is_create', select=False, states={
        'readonly': Eval('state').in_(['purchase']),
    },
                               depends=['state'])
    state = fields.Selection([
        ('draft', u'起草'),
        ('purchase', u'采购'),
    ], 'State', select=False, readonly=True)
    warehouse = fields.Many2One('stock.location', 'Warehouse', domain=[('type', '=', 'warehouse')], select=False,
                                readonly=True)
    category = fields.Many2One('product.category', 'Category', select=True)

    def get_name(self, name):
        return self.product.name

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    def get_drug_specifications(self, name):
        pool = Pool()
        try:
            product_templates = pool.get('product.template')
            product_template = product_templates.search([
                ("id", "=", int(self.product.template))
            ])
            drug_specifications = product_template[0].drug_specifications
        except:
            return None
        return drug_specifications

    def get_code(self, name):
        return self.product.code

    def get_manufacturers_describtion(self, name):
        return self.product.template.manufacturers_describtion

    def get_a_charge(self, name):
        return self.product.template.a_charge

    def get_attach(self, name):
        return self.product.template.attach

    def get_interim(self, name):
        return self.product.template.interim

    @classmethod
    def delete(cls, records):
        for value in records:
            if value.state == 'draft':
                return super(PurchaseMrpLines, cls).delete(records)
            else:
                raise Exception(u'已创建采购行项目不允许删除')
                # @classmethod
                # def create(cls, vlist):
                #     raise Exception('Create purchasing please click Create Purchase Mrp')


class CreatePurchaseAskParty(ModelView):
    'Create Purchase Ask Party'
    __name__ = 'hrp_purchase_mrp.create_purchase_ask_party'
    product = fields.Many2One('product.product', 'Product', readonly=True)
    company = fields.Many2One('company.company',
                              'Company', readonly=True)
    party = fields.Many2One('party.party', 'Supplier', required=True)


class CreatePurchase(Wizard):
    'Create Purchase'
    __name__ = 'hrp_purchase_mrp.create_purchase'
    start = StateTransition()
    ask_party = StateView('hrp_purchase_mrp.create_purchase_ask_party',
                          'hrp_purchase_mrp.create_purchase_ask_party_start', [
                              Button('Cancel', 'end', 'tryton-cancel'),
                              Button('Continue', 'start', 'tryton-go-next', default=True),
                          ])

    def transition_start(self):
        pool = Pool()
        PurchaseMrpLines = pool.get('hrp_purchase_mrp.purchase_mrp_lines')
        Purchase = pool.get('purchase.purchase')
        Date = pool.get('ir.date')
        today = str(Date.today())
        Line = pool.get('purchase.line')
        Templates = pool.get('product.template')
        Product = Pool().get('product.product')
        purchase_mrp_lines = PurchaseMrpLines.search([
            ('state', '=', 'draft'),
            ('is_create', '=', True),
            ('quantity', '!=', 0)
        ])
        if purchase_mrp_lines:
            for purchase_mrp_line in purchase_mrp_lines:
                purchases = Purchase.search([
                    ('delivery_place', '=', purchase_mrp_line.warehouse.id),
                    ('party', '=', purchase_mrp_line.party.id),
                    ('warehouse', '=', purchase_mrp_line.warehouse.id),
                    ('purchase_date', '=', purchase_mrp_line.purchase_date),
                    ('state', '=', 'draft')
                ])
                if purchases:
                    num = 0
                    line_sequence = []
                    for lines in purchases[0].lines:
                        if lines.sequence != None:
                            line_sequence.append(lines.sequence)
                        if lines.product.id == purchase_mrp_line.product.id:
                            line = Line.search([('id', '=', lines.id)])
                            quantity = lines.quantity + purchase_mrp_line.quantity
                            Line.write(line, {'quantity': quantity,
                                              'unit_price': purchase_mrp_line.product.template.cost_price})
                            num += 1
                    line_sequence.sort(reverse=True)
                    if line_sequence and line_sequence != None:
                        sequence = line_sequence[0] + 1
                    else:
                        sequence = 1
                    if num == 0:
                        purchase_line_a = {}
                        purchase_line_a['purchase'] = purchases[0].id
                        purchase_line_a['type'] = 'line'
                        purchase_line_a['sequence'] = sequence
                        purchase_line_a['product'] = purchase_mrp_line.product.id
                        purchase_line_a['quantity'] = purchase_mrp_line.quantity
                        purchase_line_a['unit'] = purchase_mrp_line.product.template.default_uom.id
                        product_template = Templates.search([
                            ("id", "=", int(purchase_mrp_line.product.template))
                        ])
                        purchase_line_a['unit_price'] = product_template[0].cost_price
                        purchase_line_a['description'] = '  '  # Product(purchase_mrp_line.product.id).rec_name
                        Line.create([purchase_line_a])
                else:
                    purchase_column = {}
                    purchase_column['party'] = purchase_mrp_line.party.id
                    purchase_column['purchase_date'] = purchase_mrp_line.purchase_date
                    purchase_column['warehouse'] = purchase_mrp_line.warehouse.id
                    purchase_column['company'] = Transaction().context['company']
                    Company = pool.get('company.company')
                    company = Company.search([('id', '=', Transaction().context['company'])])
                    purchase_column['currency'] = company[0].currency
                    purchase_column['invoice_state'] = 'none'
                    purchase_column['shipment_state'] = 'none'
                    purchase_column['state'] = 'draft'
                    purchase_column['invoice_address'] = purchase_mrp_line.party.addresses[0].id
                    purchase_column['payment_term'] = purchase_mrp_line.party.supplier_payment_term
                    purchase_id = Purchase.create([purchase_column])
                    purchase_line_b = {}
                    purchase_line_b['purchase'] = purchase_id[0].id
                    purchase_line_b['type'] = 'line'
                    purchase_line_b['sequence'] = 1
                    purchase_line_b['product'] = purchase_mrp_line.product.id
                    purchase_line_b['quantity'] = purchase_mrp_line.quantity
                    purchase_line_b['unit'] = purchase_mrp_line.product.template.default_uom.id
                    product_template = Templates.search([
                        ("id", "=", int(purchase_mrp_line.product.template))
                    ])

                    purchase_line_b['unit_price'] = product_template[0].cost_price
                    purchase_line_b['description'] = '  '  # Product(purchase_mrp_line.product.id).rec_name
                    Line.create([purchase_line_b])
                PurchaseMrpLines.write(purchase_mrp_lines, {'state': 'purchase'})
        else:
            self.raise_user_error(u'没有采购的药品')
        return 'end'


class CreatePurchaseMrpStart(ModelView):
    'Create Purchase Mrp'
    __name__ = 'hrp_purchase_mrp_create_purchase_mrp_start'
    category = fields.Many2One('product.category', 'Category', select=True, required=True)


class CreatePurchaseMrp(Wizard):
    'Create Purchase Mrp'
    __name__ = 'hrp_purchase_mrp_create_purchase_mrp'
    start = StateView('hrp_purchase_mrp_create_purchase_mrp_start',
                      'hrp_purchase_mrp.hrp_purchase_mrp_create_purchase_mrp_start_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateAction('hrp_purchase_mrp.act_purchase_mrp_lines')

    def do_create_(self, action):
        g_start = time.time()
        pre_init_start = time.time()
        pool = Pool()
        OrderPoint = pool.get('stock.order_point')
        PurchaseRreference = pool.get('hrp_order_point.purchaser_reference')
        PurchaseLines = pool.get("hrp_purchase_mrp.purchase_mrp_lines")
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        orders = OrderPoint.search([
            ('type', '=', 'purchase')
        ])
        orderpoints = []
        if not data['start']['category']:
            self.raise_user_error('Category is mandatory',
                                  'Category is mandatory')
        for i in orders:
            categories = i.product.template.categories
            for g in categories:
                if g.id == int(data['start']['category']):
                    orderpoints.append(i)
        Date = Pool().get('ir.date')
        Product = pool.get('product.product')
        Template = pool.get('product.template')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        outpatient_service = config.outpatient_service.id
        warehouse = config.warehouse.id
        hospital = config.hospital.id
        delete_list = []

        print 'pre_init_start', time.time() - pre_init_start
        # start######################################################
        # Unit = Pool().get('product.uom')

        # unit_ids = []
        # orderpoint_product_ids = []
        # for orderpoint in orderpoints:
        #     orderpoint_product_ids.append(orderpoint.product.id)
        #     # unit_ids.append(orderpoint.unit.id)
        #
        # # products = dict((product_item.id, product_item.template.id) for product_item in Product.browse(orderpoint_product_ids))
        # products = Product.read(orderpoint_product_ids)
        # # units = Unit.read(unit_ids)
        # # units = dict((orderpoint_item.id, orderpoint_item.unit.id) for orderpoint_item in )
        #
        # product_template_ids = []
        # for product_item in products:
        #     product_template_ids.append(product_item['template'])
        #
        # # product_templates = Template.read(product_template_ids)
        # product_templates = dict((pt.id, {'product_suppliers': pt.product_suppliers[0],
        #                                   'retrieve_the_code': pt.retrieve_the_code,
        #                                   'categories': pt.categories[0]
        #                                   }) for pt in Template.browse(product_template_ids))

        # Location = Pool().get('stock.location')
        init_start = time.time()
        orderpoint_product_ids = []
        for orderpoint in orderpoints:
            orderpoint_product_ids.append(orderpoint.product.id)

        product_uoms = dict((p.id, p.default_uom) for p in Product.browse(orderpoint_product_ids))
        orderpoint_products = dict((p.id, p.template.id) for p in Product.browse(orderpoint_product_ids))
        orderpoint_product_templates = dict((t.id, {'first_product_suppliers_party_id': t.product_suppliers[0].party.id,
                                                    'retrieve_the_code': t.retrieve_the_code,
                                                    'first_categorie_id': t.categories[0].id
                                                    }) for t in Template.browse(list(set(orderpoint_products.values()))))
        print 'init:', time.time() - init_start
        # end##########################################################

        for orderpoint in orderpoints:
            product = orderpoint.product.id
            with Transaction().set_context(stock_date_end=Date.today()):
                outpatient_quantities = Product.products_by_location([outpatient_service], [product], with_childs=True)
                outpatient_quantity = outpatient_quantities[(outpatient_service, product)]
                hospital_quantities = Product.products_by_location([hospital], [product], with_childs=True)
                hospital_quantity = hospital_quantities[(hospital, product)]
                warehouse_quantities = Product.products_by_location([warehouse], [product], with_childs=True)
                warehouse_quantity = warehouse_quantities[(warehouse, product)]
            purchase_quantity = PurchaseRreference.search([
                ('product', '=', product),
                ('warehouse', '=', warehouse)
            ])
            lv = {}
            # lv['party'] = orderpoint.product.template.product_suppliers[0].party.id
            # lv['product'] = orderpoint.product.id
            # lv['retrieve_the_code'] = orderpoint.product.template.retrieve_the_code
            # lv['uom'] = orderpoint.unit.id
            # lv['quantity'] = 0
            # lv['is_create'] = False
            # lv['state'] = 'draft'
            # lv['outpatient_stock'] = outpatient_quantity
            # lv['hospitalized_stock'] = hospital_quantity
            # lv['stock_level'] = warehouse_quantity
            # lv['purchase_date'] = Date.today()
            # lv['category'] = orderpoint.product.template.categories[0].id
            # lv['warehouse'] = orderpoint.warehouse_location.id
            # lv['hospitalized_7days'] = purchase_quantity[0].fourteen_days
            # lv['outpatient_7days'] = purchase_quantity[0].seven_days

            ############################################
            loop_all_start = time.time()

            # party_start = time.time()
            # lv['party'] = orderpoint.product.template.product_suppliers[0].party.id
            # party_end = time.time()
            # print 'party_past', party_end - party_start

            lv['party'] = orderpoint_product_templates[orderpoint_products[orderpoint.product.id]]['first_product_suppliers_party_id']
            lv['product'] = orderpoint.product.id
            lv['retrieve_the_code'] = orderpoint_product_templates[orderpoint_products[orderpoint.product.id]]['retrieve_the_code']
            lv['uom'] = product_uoms[orderpoint.product.id]
            lv['quantity'] = 0
            lv['is_create'] = False
            lv['state'] = 'draft'
            lv['outpatient_stock'] = outpatient_quantity
            lv['hospitalized_stock'] = hospital_quantity
            lv['stock_level'] = warehouse_quantity
            lv['purchase_date'] = Date.today()
            lv['category'] = orderpoint_product_templates[orderpoint_products[orderpoint.product.id]]['first_categorie_id']

            w_start = time.time()
            lv['warehouse'] = orderpoint.warehouse_location
            v_end = time.time()
            print 'warehouse:', time.time() - w_start

            lv['hospitalized_7days'] = purchase_quantity[0].fourteen_days
            lv['outpatient_7days'] = purchase_quantity[0].seven_days

            loop_all_end = time.time()
            loop_all_past = loop_all_end - loop_all_start
            print 'loop_all_past', loop_all_past
            ############################################
            if orderpoint.upper_period == '7':
                quantity_orderpoint = float(
                    purchase_quantity[0].one_biggest.split(',')[0].encode('utf-8')) - warehouse_quantity
                if quantity_orderpoint < 0:
                    lv['advice_quantity'] = 0
                else:
                    lv['advice_quantity'] = quantity_orderpoint
            else:
                quantity_orderpoint = float(purchase_quantity[0].one_biggest.split(',')[1]) - warehouse_quantity
                if quantity_orderpoint < 0:
                    lv['advice_quantity'] = 0
                else:
                    lv['advice_quantity'] = quantity_orderpoint

            purchaseline = PurchaseLines.search([
                ('product', '=', orderpoint.product.id),
                ('state', '=', 'draft'),
            ])
            if purchaseline:
                delete_list.append(purchaseline[0].id)
                PurchaseLines.write(purchaseline, lv)
            else:
                pruchase_lines = PurchaseLines.create([lv])
                delete_list.append(pruchase_lines[0].id)
        delete_line = PurchaseLines.search([
            ('id', 'not in', delete_list),
            ('state', '=', 'draft'),
        ])
        PurchaseLines.delete(delete_line)
        g_end = time.time()
        print 'g:',g_start - g_end
        return action, {}


class Lot:
    "Stock Lot"
    __metaclass__ = PoolMeta
    __name__ = 'stock.lot'
    hrp_quantity = fields.Function(fields.Char('Hrp Quantity'), 'get_hrp_quantity', searcher='search_hrp_quantity')  # 大
    min_quantity = fields.Function(fields.Char('Hrp Quantity'), 'get_min_quantity', searcher='search_hrp_quantity')  # 小
    hrp_forecast_quantity = fields.Function(fields.Char('Hrp Forecast Quantity'), 'get_hrp_forecast_quantity',
                                            searcher='search_hrp_quantity')  # 大
    min_forecast_quantity = fields.Function(fields.Char('Hrp Forecast Quantity'), 'get_min_forecast_quantity',
                                            searcher='search_hrp_quantity')  # 小
    date_of_production = fields.Date('date of production', required=True)

    @classmethod
    def __setup__(cls):
        super(Lot, cls).__setup__()
        cls._order[0] = ('id', 'DESC')

    @classmethod
    def write(cls, records, values, *args):

        if 'product' in values:
            cls.raise_user_error(u'药品名称不允许修改！')
        else:
            return super(Lot, cls).write(records, values)

    @classmethod
    def search_hrp_quantity(cls, lots, name):
        pass

    @classmethod
    def get_min_forecast_quantity(cls, lots, name):
        Date = Pool().get('ir.date')
        Uom = Pool().get('product.uom')
        location_ids = Transaction().context.get('locations')
        products = list(set(l.product for l in lots))
        product_ids = products and [p.id for p in products] or None
        record_ids = [r.id for r in lots]
        try:
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location(location_ids, product_ids, with_childs=True,
                                                   grouping=('product', 'lot'))
                min_quantity = {}
                for i in record_ids:
                    quantity = pbl[(location_ids[0], product_ids[0], i)]
                    min_quantity[i] = str(Uom.compute_qty(lots[0].product.template.default_uom, quantity,
                                                          lots[0].product.template.min_Package)) + lots[
                                          0].product.template.min_Package.name
                return min_quantity
        except:
            quantities = dict.fromkeys(record_ids, None)
            return quantities

    @classmethod
    def get_hrp_forecast_quantity(cls, lots, name):
        Date = Pool().get('ir.date')
        location_ids = Transaction().context.get('locations')
        products = list(set(l.product for l in lots))
        product_ids = products and [p.id for p in products] or None
        record_ids = [r.id for r in lots]
        try:
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location(location_ids, product_ids, with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = {}
                for i in record_ids:
                    quantity = pbl[(location_ids[0], product_ids[0], i)]
                    hrp_quantity[i] = str(quantity) + lots[0].product.template.default_uom.name
                return hrp_quantity
        except:
            quantities = dict.fromkeys(record_ids, None)
            return quantities

    @classmethod
    def get_min_quantity(cls, lots, name):
        Date = Pool().get('ir.date')
        Uom = Pool().get('product.uom')
        location_ids = Transaction().context.get('locations')
        products = list(set(l.product for l in lots))
        product_ids = products and [p.id for p in products] or None
        record_ids = [r.id for r in lots]
        try:
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location(location_ids, product_ids, with_childs=True,
                                                   grouping=('product', 'lot'))
                min_quantity = {}
                for i in record_ids:
                    quantity = pbl[(location_ids[0], product_ids[0], i)]
                    min_quantity[i] = str(Uom.compute_qty(lots[0].product.template.default_uom, quantity,
                                                          lots[0].product.template.min_Package)) + lots[
                                          0].product.template.min_Package.name
                return min_quantity
        except:
            quantities = dict.fromkeys(record_ids, None)
            return quantities

    @classmethod
    def get_hrp_quantity(cls, lots, name):
        Date = Pool().get('ir.date')
        location_ids = Transaction().context.get('locations')
        products = list(set(l.product for l in lots))
        product_ids = products and [p.id for p in products] or None
        record_ids = [r.id for r in lots]
        try:
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location(location_ids, product_ids, with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = {}
                for i in record_ids:
                    quantity = pbl[(location_ids[0], product_ids[0], i)]
                    hrp_quantity[i] = str(quantity) + lots[0].product.template.default_uom.name
                return hrp_quantity
        except:
            quantities = dict.fromkeys(record_ids, None)
            return quantities



            # @classmethod
            # def search_hrp_quantity(cls, name, domain=None):
            #     pass
            #     # location_ids = Transaction().context.get('locations')
            #     # return cls._search_quantity(name, location_ids, domain,
            #     #     grouping=('product', 'lot'))
