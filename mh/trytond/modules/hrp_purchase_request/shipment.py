from trytond.model import ModelView, fields
from trytond.model import ModelView
from trytond.modules.stock import Location, Product
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.pyson import If, In, Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
import itertools

__all_ = ['CreateShipmentInReturn', 'NewCreatePurchaseRequest']


class CreateShipmentInReturn(ModelView):
    'CreateShipmentInReturn'
    __name__ = 'hrp_purchase_request.CreateShipmentInReturn'
    _rec_name = 'number'
    effective_date = fields.Date('Effective Date',
                                 states={
                                     'readonly': Eval('state').in_(['cancel', 'done']),
                                 },
                                 depends=['state'])
    planned_date = fields.Date('Planned Date',
                               states={
                                   'readonly': Eval('state') != 'draft',
                               }, depends=['state'])
    company = fields.Many2One('company.company', 'Company', required=True,
                              states={
                                  'readonly': Eval('state') != 'draft',
                              },
                              domain=[
                                  ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                                   Eval('context', {}).get('company', -1)),
                              ],
                              depends=['state'])
    number = fields.Char('Number', size=None, select=True, readonly=True)
    reference = fields.Char("Reference", size=None, select=True,
                            states={
                                'readonly': Eval('state') != 'draft',
                            }, depends=['state'])
    supplier = fields.Many2One('party.party', 'Supplier',
                               states={
                                   'readonly': (((Eval('state') != 'draft')
                                                 | Eval('moves', [0]))
                                                & Eval('supplier', 0)),
                               }, required=True,
                               depends=['state', 'supplier'])
    delivery_address = fields.Many2One('party.address', 'Delivery Address',
                                       states={
                                           'readonly': Eval('state') != 'draft',
                                       },
                                       domain=[
                                           ('party', '=', Eval('supplier'))
                                       ],
                                       depends=['state', 'supplier'])
    from_location = fields.Many2One('stock.location', "From Location",
                                    required=True, states={
            'readonly': (Eval('state') != 'draft') | Eval('moves', [0]),
        }, domain=[('type', 'in', ['storage', 'view'])],
                                    depends=['state'])
    to_location = fields.Many2One('stock.location', "To Location",
                                  required=True, states={
            'readonly': (Eval('state') != 'draft') | Eval('moves', [0]),
        }, domain=[('type', '=', 'supplier')],
                                  depends=['state'])
    moves = fields.One2Many('stock.move', 'shipment', 'Moves',
                            states={
                                'readonly': (((Eval('state') != 'draft') | ~Eval('from_location'))
                                             & Eval('to_location')),
                            },
                            domain=[
                                ('from_location', '=', Eval('from_location')),
                                ('to_location', '=', Eval('to_location')),
                                ('company', '=', Eval('company')),
                            ],
                            depends=['state', 'from_location', 'to_location', 'company'])
    origins = fields.Function(fields.Char('Origins'), 'get_origins')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('assigned', 'Assigned'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
    ], 'State', readonly=True)

    @staticmethod
    def default_planned_date():
        return Pool().get('ir.date').today()

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def default_warehouse(cls):
        Location = Pool().get('stock.location')
        locations = Location.search(cls.warehouse.domain)
        if len(locations) == 1:
            return locations[0].id

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('supplier')
    def on_change_supplier(self):
        self.contact_address = None
        if self.supplier:
            self.contact_address = self.supplier.address_get()

    @fields.depends('supplier')
    def on_change_with_supplier_location(self, name=None):
        if self.supplier:
            return self.supplier.supplier_location.id

    @classmethod
    def default_warehouse_input(cls):
        warehouse = cls.default_warehouse()
        if warehouse:
            return cls(warehouse=warehouse).on_change_with_warehouse_input()

    @fields.depends('warehouse')
    def on_change_with_warehouse_input(self, name=None):
        if self.warehouse:
            return self.warehouse.input_location.id

    @classmethod
    def default_warehouse_storage(cls):
        warehouse = cls.default_warehouse()
        if warehouse:
            return cls(warehouse=warehouse).on_change_with_warehouse_storage()

    @fields.depends('warehouse')
    def on_change_with_warehouse_storage(self, name=None):
        if self.warehouse:
            return self.warehouse.storage_location.id

    def get_incoming_moves(self, name):
        moves = []
        for move in self.moves:
            if move.to_location.id == self.warehouse.input_location.id:
                moves.append(move.id)
        return moves

    @classmethod
    def set_incoming_moves(cls, shipments, name, value):
        if not value:
            return
        cls.write(shipments, {
            'moves': value,
        })

    def get_inventory_moves(self, name):
        moves = []
        for move in self.moves:
            if (move.from_location.id ==
                    self.warehouse.input_location.id):
                moves.append(move.id)
        return moves

    @classmethod
    def set_inventory_moves(cls, shipments, name, value):
        if not value:
            return
        cls.write(shipments, {
            'moves': value,
        })

    @property
    def _move_planned_date(self):
        '''
        Return the planned date for incoming moves and inventory_moves
        '''
        return self.planned_date, self.planned_date

    def get_origins(self, name):
        return ', '.join(set(itertools.ifilter(None,
                                               (m.origin_name for m in self.moves))))

    @classmethod
    def _get_inventory_moves(cls, incoming_move):
        pool = Pool()
        Move = pool.get('stock.move')
        if incoming_move.quantity <= 0.0:
            return None
        move = Move()
        move.product = incoming_move.product
        move.uom = incoming_move.uom
        move.quantity = incoming_move.quantity
        move.from_location = incoming_move.to_location
        move.to_location = incoming_move.shipment.warehouse.storage_location
        move.state = Move.default_state()
        # Product will be considered in stock only when the inventory
        # move will be made:
        move.planned_date = None
        move.company = incoming_move.company
        return move

    @classmethod
    def create_inventory_moves(cls, shipments):
        for shipment in shipments:
            # Use moves instead of inventory_moves because save reset before
            # adding new records and as set_inventory_moves is just a proxy to
            # moves, it will reset also the incoming_moves
            moves = list(shipment.moves)
            for incoming_move in shipment.incoming_moves:
                move = cls._get_inventory_moves(incoming_move)
                if move:
                    moves.append(move)
            shipment.moves = moves
            shipment.save()
