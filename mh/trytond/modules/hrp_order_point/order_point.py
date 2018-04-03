# coding:utf-8
from trytond.model import ModelView, ModelSQL, fields, Check
from trytond.pyson import If, Equal, Eval, Not, In
from trytond.transaction import Transaction
from trytond import backend
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelView, ModelSQL, fields
from ..stock_supply import order_point
from datetime import datetime, timedelta

__all__ = ['OrderPoint', 'PurchaseRreference']

price_digits = (16, 2)


class OrderPoint:
    "Order Point"
    __metaclass__ = PoolMeta
    __name__ = 'stock.order_point'
    secondary = fields.Many2One('stock.location', 'Secondary',
                                select=True,
                                domain=[('type', '=', 'warehouse'),
                                        ('storage_location', '!=', Eval('provisioning_location'))],
                                states={
                                    'invisible': Not(Equal(Eval('type'), 'internal')),
                                    'required': Equal(Eval('type'), 'internal'),
                                },
                                depends=['type', 'provisioning_location'])
    retrieve_the_code = fields.Function(fields.Char('Retrieve_the_code', select=True, readonly=True),
                                        'get_retrieve_the_code')
    drug_specifications = fields.Function(fields.Char('Drug_specifications', select=True, readonly=True),
                                          'get_drug_specifications')
    attach = fields.Function(fields.Char('Attach', select=True, readonly=True), 'get_attach')
    a_charge = fields.Function(fields.Integer('A_charge', select=True, readonly=True), 'get_a_charge')
    interim = fields.Function(fields.Selection([
        ('1', u''),
        ('2', u'是')], 'interim', select=True, readonly=True), 'get_interim')
    upper_period = fields.Selection([
        ('7', u'7天消耗量'),
        ('14', u'14天消耗量')
    ], 'upper_period', select=True, required=True, sort=False)
    code = fields.Function(fields.Char('Code', readonly=True, select=True), 'get_code')
    name = fields.Function(fields.Char('Name', readonly=True, select=True), 'get_name')

    @classmethod
    def __setup__(cls):
        super(OrderPoint, cls).__setup__()
        cls._order = [
            ('product', 'ASC'),
        ]

    def get_code(self, name):
        return self.product.code

    def get_name(self, name):
        return self.product.name

    @staticmethod
    def default_upper_period():
        return '7'

    @staticmethod
    def default_secondary():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        purchase_configuration = UserId.get_user_warehouse()
        if purchase_configuration == None:
            raise ValueError(u'请填写产品配置')
        else:
            return purchase_configuration

    @staticmethod
    def default_warehouse_location():
        if Transaction().user == 1:
            purchase_configurations = Pool().get('purchase.configuration')
            purchase_configuration = purchase_configurations.search([])
            purchase_configuration = int(purchase_configuration[0].warehouse)
            if purchase_configuration == None:
                raise ValueError(u'请填写产品配置')
            else:
                return purchase_configuration
        else:
            pass

    @staticmethod
    def default_max_quantity():
        return 0.00

    @staticmethod
    def default_min_quantity():
        return 0.00

    @staticmethod
    def default_type():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        user_id = UserId.get_user_warehouse()
        if user_id == 1:
            return 'purchase'  # 中心药库
        elif user_id == config.warehouse.id:
            return 'purchase'
        else:
            return 'internal'

    @fields.depends('secondary')
    def on_change_secondary(self):
        if self.secondary:
            Location = Pool().get('stock.location')
            location = Location.search([('id', '=', self.secondary.id)])
            storage_location = location[0].storage_location.id
            self.storage_location = storage_location

    def get_warehouse_secondary(self, name):
        pass

    def get_retrieve_the_code(self, name):
        return self.product.template.retrieve_the_code

    def get_drug_specifications(self, name):
        return self.product.template.drug_specifications

    def get_attach(self, name):
        return self.product.template.attach

    def get_a_charge(self, name):
        return self.product.template.a_charge

    def get_interim(self, name):
        return self.product.interim

    @classmethod
    def create(cls, vlist):
        Product = Pool().get('product.product')
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        UserId.get_user_id()
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        user_id = UserId.get_user_warehouse()
        for each in vlist:
            type = cls.default_get(['type'], with_rec_name=False)
            if Product(each['product']).template.is_direct_sending == True and type['type'] == 'purchase':
                cls.raise_user_error(u'该药品为药房直送，不能创建药库订货点！')
            if user_id == 1:
                OrderPoint.create_('purchase', each['product'])
            elif user_id == config.warehouse.id:
                OrderPoint.create_('purchase', each['product'])
            else:
                OrderPoint.create_('internal', each['product'], each['storage_location'])
        return super(OrderPoint, cls).create(vlist)

    @classmethod
    def create_(cls, type_, product, storage_location=None, record_id=0, genre=False, ):
        Date = Pool().get('ir.date')
        PurchaserReference = Pool().get('hrp_order_point.purchaser_reference')
        Location = Pool().get('stock.location')
        ShipmentOut = Pool().get('stock.shipment.out')  # 客户交货
        ShipmentOutReturn = Pool().get('stock.shipment.out.return')  # 客户退货
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        outpatient_service = config.outpatient_service.id
        hospital = config.hospital.id
        warehouse = config.warehouse.id
        today = Date.today()
        seven_day = today - timedelta(days=7)
        fourteen_day = today - timedelta(days=14)
        if type_ == 'internal':
            childs = Location.search([('id', '=', storage_location)])
            if genre == False:
                parent = childs[0].parent.id
                output_location = childs[0].parent.output_location.id
            else:
                parent = storage_location
                output_location = childs[0].output_location.id
            seven_days = ShipmentOut.search([
                ('effective_date', '>=', seven_day),
                ('effective_date', '<', today),
                ('state', '=', 'done'),
                ('warehouse', '=', parent)])

            fourteen_days = ShipmentOut.search([
                ('warehouse', '=', parent),
                ('state', '=', 'done'),
                ('effective_date', '<', today),
                ('effective_date', '>=', fourteen_day)])

            seven_days_sum = 0
            if seven_days != []:
                for sevendays in seven_days:
                    moves = sevendays.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_location and move.product.id == product:
                            sum += move.quantity
                    seven_days_sum += sum
            fourteen_days_sum = 0
            if fourteen_days != []:
                for fourteendays in fourteen_days:
                    moves = fourteendays.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_location and move.product.id == product:
                            sum += move.quantity
                    fourteen_days_sum += sum
            if genre == True:
                purchaserreference = PurchaserReference.search([('id', '=', record_id)])
                PurchaserReference.write(purchaserreference, {
                    'seven_days': seven_days_sum,
                    'fourteen_days': fourteen_days_sum})
            else:
                purchaserreference = PurchaserReference.search([('product', '=', product), ('warehouse', '=', parent,)])
                if purchaserreference == []:
                    PurchaserReference.create([{'product': product,
                                                'warehouse': parent,
                                                'is_level': False,
                                                'seven_days': seven_days_sum,
                                                'fourteen_days': fourteen_days_sum}])
                else:
                    PurchaserReference.write(purchaserreference, {
                        'seven_days': seven_days_sum,
                        'fourteen_days': fourteen_days_sum})
        else:
            output_location = config.hospital.output_location.id
            output_location1 = config.outpatient_service.output_location.id
            all_seven_warehouse = ShipmentOut.search([
                ('effective_date', '>=', seven_day),
                ('effective_date', '<', today),
                ('state', '=', 'done'),
                ('warehouse', '!=', warehouse)])

            all_seven_warehouse_sum = 0
            if all_seven_warehouse != []:
                for All_seven_warehouse in all_seven_warehouse:
                    output_locations = All_seven_warehouse.warehouse.output_location.id
                    moves = All_seven_warehouse.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_locations and move.product.id == product:
                            sum += move.quantity
                    all_seven_warehouse_sum += sum
            all_fourteen_warehouse = ShipmentOut.search([
                ('effective_date', '>=', fourteen_day),
                ('effective_date', '<', today),
                ('state', '=', 'done'),
                ('warehouse', '!=', warehouse)])
            all_fourteen_warehouse_sum = 0
            if all_fourteen_warehouse != []:
                for All_fourteen_warehouse in all_fourteen_warehouse:
                    output_locations = All_fourteen_warehouse.warehouse.output_location.id
                    moves = All_fourteen_warehouse.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_locations and move.product.id == product:
                            sum += move.quantity
                    all_fourteen_warehouse_sum += sum
            all_consumption = str(all_seven_warehouse_sum) + ',' + str(all_fourteen_warehouse_sum)

            seven_days_hospital = ShipmentOut.search([
                ('effective_date', '>=', seven_day),
                ('effective_date', '<', today),
                ('state', '=', 'done'),
                ('warehouse', '=', hospital)])
            seven_days_outpatient_service = ShipmentOut.search([
                ('warehouse', '=', outpatient_service),
                ('state', '=', 'done'),
                ('effective_date', '<', today),
                ('effective_date', '>=', seven_day)])

            seven_days_hospital_sum = 0
            if seven_days_hospital != []:
                for seven_days_hospitals in seven_days_hospital:
                    moves = seven_days_hospitals.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_location and move.product.id == product:
                            sum += move.quantity
                    seven_days_hospital_sum += sum
            seven_days_outpatient_service_sum = 0
            if seven_days_outpatient_service != []:
                for seven_days_outpatient_services in seven_days_outpatient_service:
                    moves = seven_days_outpatient_services.moves
                    sum = 0
                    for move in moves:
                        if move.to_location.id == output_location1 and move.product.id == product:
                            sum += move.quantity
                    seven_days_outpatient_service_sum += sum
            if genre == True:
                purchaserreference = PurchaserReference.search([('id', '=', record_id)])
                PurchaserReference.write(purchaserreference, {
                    'seven_days': seven_days_outpatient_service_sum,
                    'fourteen_days': seven_days_hospital_sum,
                    'one_biggest': all_consumption})
            else:
                purchaserreference = PurchaserReference.search(
                    [('product', '=', product), ('warehouse', '=', warehouse,)])
                if purchaserreference == []:
                    PurchaserReference.create([{'product': product,
                                                'warehouse': warehouse,
                                                'is_level': True,
                                                'seven_days': seven_days_outpatient_service_sum,
                                                'fourteen_days': seven_days_hospital_sum,
                                                'one_biggest': all_consumption}])
                else:
                    PurchaserReference.write(purchaserreference, {
                        'seven_days': seven_days_outpatient_service_sum,
                        'fourteen_days': seven_days_hospital_sum,
                        'one_biggest': all_consumption
                    })

    @fields.depends('product')
    def on_change_product(self):
        pool = Pool()
        Date_ = pool.get('ir.date')
        Product = pool.get('product.product')
        self.unit = None
        self.unit_digits = 2
        if self.product:
            products = Product.search([
                ('id', '=', self.product.id)
            ])
            self.drug_specifications = products[0].drug_specifications
            self.retrieve_the_code = products[0].retrieve_the_code
            self.attach = products[0].attach
            self.a_charge = products[0].a_charge
            self.is_direct_sending = products[0].is_direct_sending
            self.unit = self.product.default_uom
            self.unit_digits = self.product.default_uom.digits
            self.interim = products[0].interim
            self.code = self.product.code

    @fields.depends('type')
    def on_change_type(self):
        if self.type == 'internal':
            Location = Pool().get('stock.location')
            purchase_configurations = Pool().get('purchase.configuration')
            purchase_configuration = purchase_configurations.search([])
            purchase_configuration = purchase_configuration[0].warehouse
            location = Location.search([('id', '=', purchase_configuration.id)])
            storage_location = location[0].storage_location.id
            if storage_location == None:
                raise ValueError('Please fill in the product configuration')
            else:
                self.warehouse_location = None
                self.provisioning_location = storage_location
        else:
            purchase_configurations = Pool().get('purchase.configuration')
            purchase_configuration = purchase_configurations.search([])
            purchase_configuration = int(purchase_configuration[0].warehouse)
            if purchase_configuration == None:
                raise ValueError('Please fill in the product configuration')
            else:
                self.warehouse_location = purchase_configuration

    # @classmethod
    # def write(cls, records, values, *args):
    #     if values.keys() != ['upper_period']:
    #         raise ValueError('Not allowed to change')
    #     else:
    #         return super(OrderPoint, cls).write(records, values)
    @classmethod
    def write_(cls):
        OrderPoint = Pool().get('stock.order_point')
        PurchaserReference = Pool().get('hrp_order_point.purchaser_reference')
        purchaserreference = PurchaserReference.search([])
        for reference in purchaserreference:
            if reference.is_level == False:
                OrderPoint.create_('internal', reference.product.id, reference.warehouse.id, reference.id, genre=True)
            else:
                OrderPoint.create_('purchase', reference.product.id, reference.warehouse.id, reference.id, genre=True)


class PurchaseRreference(ModelSQL, ModelView):
    'Purchase Rreference'
    __name__ = "hrp_order_point.purchaser_reference"
    product = fields.Many2One('product.product', 'product', select=True, required=True)
    warehouse = fields.Many2One('stock.location', "Warehouse", domain=[('type', '=', 'warehouse')], required=True)
    seven_days = fields.Integer('Seven days', select=True, required=True)
    fourteen_days = fields.Integer('Fourteen days', select=True, required=True)
    one_biggest = fields.Char('One Biggest', select=True)
    is_level = fields.Boolean('Is Level', select=True)
