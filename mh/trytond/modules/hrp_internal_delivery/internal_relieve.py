#coding:utf-8
from trytond.model import Workflow
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView,Button, StateAction

__all__ = ['InternalRelieve','InternalRelieveWizard']

####################    冻结转非限制    ####################################

class InternalRelieve(ModelView):
    'InternalRelieve'
    __name__ = 'hrp_internal_delivery.internal_relieve'
    _rec_name = 'number'

    reference = fields.Char("Reference", size=None, select=True,
    states={
        'readonly': Eval('state') != 'draft',
        }, depends=['state'])
    number = fields.Char('Number', size=None, select=True, readonly=True)
    effective_date = fields.Date('Effective Date',
        states={
            'readonly': Eval('state').in_(['cancel', 'done']),
            },
        depends=['state'])
    planned_date = fields.Date('Planned Date',
        states={
            'readonly': Eval('state') != 'draft',
            }, depends=['state'])
    company = fields.Many2One('company.company', 'Company', required=True)
    from_location = fields.Many2One('stock.location', "From Location",
        required=True, states={
            'readonly': (Eval('state') != 'draft') | Eval('moves', [0]),
            },
        domain=[
            ('type', 'in', ['view', 'storage', 'lost_found']),
            ], depends=['state'])
    to_location = fields.Many2One('stock.location', "To Location",
        required=True, states={
            'readonly': (Eval('state') != 'draft') | Eval('moves', [0]),
            }, domain=[
            ('type', 'in', ['view', 'storage', 'lost_found']),
            ], depends=['state'])
    actives = fields.Selection([
        ('03', u'冻结转非限制'),
        ], 'active', readonly=True)
    moves = fields.One2Many('stock.move', 'shipment', 'Moves',
    states={
        'readonly': (Eval('state').in_(['cancel', 'assigned', 'done'])
            | ~Eval('from_location') | ~Eval('to_location')),
        },
    domain=[
        If(Eval('state') == 'draft', [
                ('from_location', '=', Eval('from_location')),
                ('to_location', '=', Eval('to_location')),
                ('starts', '=', Eval('actives')),
                ], [
                ('from_location', 'child_of', [Eval('from_location', -1)],
                    'parent'),
                ('to_location', 'child_of', [Eval('to_location', -1)],
                    'parent'),
                ]),
                ('starts', 'child_of', [Eval('actives', -1)],
                    'parent'),
        ('company', '=', Eval('company')),
        ],
    depends=['state', 'from_location', 'to_location', 'planned_date',
        'company','actives'])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('assigned', 'Assigned'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ], 'State', readonly=True)

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_actives():
        return '03'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('stock.configuration')
        vlist = [x.copy() for x in vlist]
        config = Config(1)
        for values in vlist:
            if values.get('number') is None:
                values['number'] = Sequence.get_id(
                        config.shipment_internal_sequence.id)
        return super(InternalRelieve, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        # Cancel before delete
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalRelieve, cls).delete(shipments)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, shipments):
        Move = Pool().get('stock.move')
        # First reset state to draft to allow update from and to location
        Move.draft([m for s in shipments for m in s.moves
                if m.state != 'staging'])
        for shipment in shipments:
            Move.write([m for m in shipment.moves
                    if m.state != 'done'], {
                    'from_location': shipment.from_location.id,
                    'to_location': shipment.to_location.id,
                    'planned_date': shipment.planned_date,
                    })

    @classmethod
    @ModelView.button
    @Workflow.transition('waiting')
    def wait(cls, shipments):
        Move = Pool().get('stock.move')
        Move.draft([m for s in shipments for m in s.moves])
        moves = []
        for shipment in shipments:
            for move in shipment.moves:
                if move.state != 'done':
                    move.planned_date = shipment.planned_date
                    moves.append(move)
        Move.save(moves)

    @classmethod
    @Workflow.transition('assigned')
    def assign(cls, shipments):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, shipments):
        pool = Pool()
        Move = pool.get('stock.move')
        Date = pool.get('ir.date')
        Move.do([m for s in shipments for m in s.moves])
        cls.write([s for s in shipments if not s.effective_date], {
                'effective_date': Date.today(),
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, shipments):
        Move = Pool().get('stock.move')
        Move.cancel([m for s in shipments for m in s.moves])

    @classmethod
    @ModelView.button_action('stock.wizard_shipment_internal_assign')
    def assign_wizard(cls, shipments):
        pass


    @ModelView.button
    def assign_try(cls, shipments):
        Move = Pool().get('stock.move')
        to_assign = [m for s in shipments for m in s.moves
            if m.from_location.type != 'lost_found']
        if not to_assign or Move.assign_try(to_assign):
            cls.assign(shipments)
            return True
        else:
            return False

class InternalRelieveWizard(Wizard):
    __name__ = 'hrp_internal_delivery.internal_relieve_wizard'

    start = StateView('hrp_internal_delivery.internal_relieve',
        'hrp_internal_delivery.internal_relieve_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('stock.act_internal_relieve')
    def do_create_(self, action):
        internal = Pool().get('hrp_internal_delivery.shipment.internal')
        data = {}
        for state_name,state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        lv = {}
        lv['to_location'] = data['start']['to_location']
        lv['reference'] = data['start']['reference']
        lv['from_location'] = data['start']['from_location']
        lv['planned_date'] = data['start']['planned_date']
        lv['company'] = data['start']['company']
        lv['number'] = data['start']['number']
        lv['state'] = data['start']['state']
        Move = data['start']['moves']
        list = []
        for each in Move:
            dict = {}
            dict['starts'] = each['starts']
            dict['origin'] = each['origin']
            dict['to_location'] = each['to_location']
            dict['product'] = each['product']
            dict['from_location'] = each['from_location']
            dict['invoice_lines'] = each['invoice_lines']
            dict['is_direct_sending'] = each['is_direct_sending']
            dict['planned_date'] = each['planned_date']
            dict['company'] = each['company']
            dict['unit_price'] = each['unit_price']
            dict['currency'] = each['currency']
            dict['lot'] = each['lot']
            dict['uom'] = each['uom']
            dict['quantity'] = each['quantity']
            list.append(dict)
            lv['moves'] = [['create',list]]
            lv['effective_date'] = data['start']['effective_date']
        internal.create([lv])
        return action,{}

