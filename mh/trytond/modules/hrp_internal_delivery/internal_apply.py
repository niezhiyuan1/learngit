# coding:utf-8
import time
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Equal, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['InternalApply', 'InternalApplyWizard', 'Move', 'TestApply']

LOCATION_DEPENDS = ['state']
DEPENDS = ['state']
STATES = {
    'readonly': ~Eval('is_collar', True),
}


class TestApply(ModelView):
    """Test Apply"""

    __name__ = 'hrp_internal_delivery.test_apply'
    _rec_name = 'number'

    product = fields.Many2One("product.product", "Product", required=True)  # 产品
    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    company = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    odd_numbers = fields.Char('odd_numbers', select=True, readonly=True)  # 建议请领数量
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Char('stock_level', select=True, readonly=True)  # 现有库存量
    outpatient_7days = fields.Char('Outpatient_7days', select=True, readonly=True)  # 7日量
    proposal = fields.Float('proposal', select=True, states=STATES
                            , depends=['is_direct_sending'])  # 请领数量
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    is_collar = fields.Boolean('is_collar', select=True)  # 是否请领
    party = fields.Many2One('party.party', 'Party', select=True)  # 供应商
    unit_price = fields.Numeric('unit_price', digits=(16, 4))  # 价格

    parent = fields.Many2One('hrp_internal_delivery.internal_apply', 'parent', select=True)

    @staticmethod
    def default_is_collar():
        return False


class InternalApply(ModelView):
    'Internal Apply'

    __name__ = 'hrp_internal_delivery.internal_apply'
    _rec_name = 'number'

    number = fields.Char('Number', size=None, select=True)
    type = fields.Selection(
        [
            ('00', u'常规药请领单'),
            ('06', u'直送药请领单'),
            ('2017', u' '),
        ],
        'Type', select=True, required=True, states={
            'readonly': Bool(Eval('moves'))})

    starts = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('07', u'同位素'),
    ], 'Starts', sort=False, select=True, states={
        'invisible': Equal(Eval('type'), '2017')
    }, )

    medicine = fields.Selection([
        ('00', u''),
        ('2', u'临采'),
        ('02', u'精一'),
        ('03', u'麻醉'),
    ], 'medicine', select=True,
        # states={
        #     'invisible':~Equal(Eval('starts'),'00')| Equal(Eval('type'),'06')
        #     },
    )
    special = fields.Selection([
        ('00', u'直送'),
    ], 'special', select=True
        , states={
            'readonly': Equal(Eval('type'), '06'),
            'invisible': ~Equal(Eval('type'), '06'),
        },
        depends=['type'],
    )
    planned_date = fields.Date('Planned Date', readonly=True)

    moves = fields.One2Many('hrp_internal_delivery.test_apply', 'parents', 'Moves')
    from_location = fields.Many2One('stock.location', 'from_location', readonly=True)
    to_location = fields.Many2One('stock.location', 'to_location', readonly=True)
    warehouse_to_location = fields.Many2One('stock.location', 'warehouse_to_location', select=True)

    # change_state = fields.Boolean('change_state',select=True)#更改请领状态

    @staticmethod
    def default_type():
        return '2017'

    @staticmethod
    def default_from_location():
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        return config.warehouse.storage_location.id  # 默认为中心药房

    @staticmethod
    def default_to_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @staticmethod
    def default_planned_date():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

    @fields.depends('type')
    def on_change_type(self):
        if self.type == '06':
            self.special = '00'
        else:
            pass

    @fields.depends('starts', 'moves', 'special', 'to_location', 'medicine')
    def on_change_starts(self):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        MOVE = Pool().get('hrp_new_product.new_product')
        list = []
        if self.special == None:
            locals = self.to_location
            if self.medicine == None:
                mmm = MOVE.search([
                    ('interim', 'in', ['1', '00']),
                    ('drug_type', '=', self.starts),
                    ('is_direct_sending', '=', False),
                    ('to_location', '=', locals),
                ])
            else:
                if self.medicine == '2':
                    mmm = MOVE.search([
                        ('drug_type', '=', self.starts),
                        ('is_direct_sending', '=', False),
                        ('to_location', '=', locals),
                        ('interim', 'in', ['2', '01']),
                    ])
                else:
                    mmm = MOVE.search([
                        ('drug_type', '=', self.starts),
                        ('is_direct_sending', '=', False),
                        ('to_location', '=', locals),
                        ('interim', '=', self.medicine),
                    ])
            for i in mmm:
                dict = {}
                dict['code'] = i.code
                dict['product'] = i.product.id
                dict['product_name'] = i.product.name
                dict['drug_specifications'] = i.drug_specifications
                dict['company'] = i.uom
                dict['a_charge'] = i.a_charge
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([locals], [i.product.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0.0
                dict['stock_level'] = str(stock_level)
                outpatient_ = str(i.outpatient_7days)
                dict['outpatient_7days'] = outpatient_.ljust(5, ' ')
                stock_levels = float(i.outpatient_7days) - stock_level
                if stock_levels <= 0:
                    dict['odd_numbers'] = '0.0'
                else:
                    dict['odd_numbers'] = str(stock_levels)
                dict['is_direct_sending'] = i.is_direct_sending
                dict['lot'] = i.lot
                dict['is_collar'] = False
                dict['party'] = i.party
                dict['unit_price'] = i.unit_price
                list.append(dict)
            self.moves = list
        if self.special == '00':
            locals = self.to_location
            mmm = MOVE.search([
                ('drug_type', '=', self.starts),
                ('is_direct_sending', '=', True),
                ('to_location', '=', locals),
            ])
            for i in mmm:
                dict = {}
                dict['code'] = i.code
                dict['product'] = i.product.id
                dict['product_name'] = i.product.name
                dict['drug_specifications'] = i.drug_specifications
                dict['company'] = i.uom
                dict['odd_numbers'] = i.odd_numbers
                dict['a_charge'] = i.a_charge
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([locals], [i.product.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0.0
                dict['stock_level'] = str(stock_level)
                if i.outpatient_7days == 0:
                    dict['outpatient_7days'] = '0.0'
                else:
                    dict['outpatient_7days'] = str(i.outpatient_7days)
                stock_levels = i.outpatient_7days - stock_level
                if stock_levels <= 0:
                    dict['odd_numbers'] = '0.0'
                else:
                    dict['odd_numbers'] = stock_levels
                dict['is_direct_sending'] = i.is_direct_sending
                dict['lot'] = i.lot
                dict['is_collar'] = i.is_collar
                dict['party'] = i.party
                dict['unit_price'] = i.unit_price
                list.append(dict)
            self.moves = list

    # 西药特殊，精神一，麻醉
    @fields.depends('medicine', 'moves', 'starts', 'special', 'to_location')
    def on_change_medicine(self):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        MOVE = Pool().get('hrp_new_product.new_product')
        list = []
        locals = self.to_location
        if self.special == None:
            search_move = MOVE.search([
                ('is_direct_sending', '=', False),
                ('interim', '=', self.medicine),
                ('drug_type', '=', self.starts),
                ('to_location', '=', locals),
            ])
            for i in search_move:
                dict = {}
                dict['code'] = i.code
                dict['product'] = i.product.id
                dict['product_name'] = i.product.name
                dict['drug_specifications'] = i.drug_specifications
                dict['company'] = i.uom
                dict['a_charge'] = i.a_charge
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([locals], [i.product.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0.0
                dict['stock_level'] = str(stock_level)
                Ljust = str(i.outpatient_7days)
                dict['outpatient_7days'] = Ljust.ljust(5, ' ')
                stock_levels = float(i.outpatient_7days) - stock_level
                if stock_levels <= 0:
                    dict['odd_numbers'] = '0.0'
                else:
                    dict['odd_numbers'] = str(stock_levels)
                dict['is_direct_sending'] = i.is_direct_sending
                dict['lot'] = i.lot
                dict['is_collar'] = i.is_collar
                dict['party'] = i.party
                dict['unit_price'] = i.unit_price
                list.append(dict)
        if self.starts == None:
            pass
        if self.special == '00':
            locals = self.to_location
            search_move = MOVE.search([
                ('drug_type', '=', self.starts),
                ('interim', '=', self.medicine),
                ('is_direct_sending', '=', True),
                ('to_location', '=', locals),
            ])
            for i in search_move:
                dict = {}
                dict['code'] = i.code
                dict['product'] = i.product.id
                dict['product_name'] = i.product.name
                dict['drug_specifications'] = i.drug_specifications
                dict['company'] = i.uom
                dict['odd_numbers'] = i.odd_numbers
                dict['a_charge'] = i.a_charge
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([locals], [i.product.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0.0
                dict['stock_level'] = str(stock_level)
                dict['outpatient_7days'] = i.outpatient_7days
                stock_levels = i.outpatient_7days - stock_level
                if stock_levels <= 0:
                    dict['odd_numbers'] = '0.0'
                else:
                    dict['odd_numbers'] = stock_levels
                dict['is_direct_sending'] = i.is_direct_sending
                dict['lot'] = i.lot
                dict['is_collar'] = i.is_collar
                dict['party'] = i.party
                dict['unit_price'] = i.unit_price
                list.append(dict)
        self.moves = list

    @staticmethod
    def default_actives():
        return '00'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Date_(object):
    @classmethod
    def today(cls):
        pass


class InternalApplyWizard(Wizard):
    'Internal Apply Wizard'

    __name__ = 'hrp_internal_delivery.internal_apply_wizard'

    start = StateView('hrp_internal_delivery.internal_apply',
                      'hrp_internal_delivery.internal_apply_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_hrp_internal_delivery')

    def do_create_(self, action):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        internal = Pool().get('stock.shipment.internal')
        data = {}
        ZY = config.hospital.storage_location.id  # 住院药房
        MZ = config.outpatient_service.storage_location.id  # 门诊药房
        TJ = config.medical.storage_location.id  # 体检药房
        NJ = config.endoscopic.storage_location.id  # 内镜药房
        ZJ = config.preparation.storage_location.id  # 制剂室
        FS = config.ward.storage_location.id  # 放射科
        CY = config.herbs.storage_location.id  # 草药房
        date = time.strftime('%Y%m', time.localtime())
        sequence_dict = {ZY: 'B', MZ: 'X', TJ: 'T', NJ: 'N', ZJ: 'J', FS: 'F', CY: 'C'}
        Keys = sequence_dict.keys()
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        list_straights = []
        lv = {}
        lv['starts'] = data['start']['type']
        lv['company'] = 1
        lv['to_location'] = config.transfers.id  # 中转库存地transfers
        lv['from_location'] = data['start']['from_location']
        lv['place_of_service'] = data['start']['to_location']
        lv['planned_date'] = data['start']['planned_date']
        lv['drug_starts'] = data['start']['starts']
        lv['state'] = u'draft'
        Move = data['start']['moves']
        if data['start']['type'] == '00':
            state = '00'
        else:
            state = '06'
        if data['start']['type'] == '00':
            list_branch = []
            list = []
            for each in Move:
                if each['is_collar'] == True:
                    list_branch.append(1)
                    dict = {}
                    dict['origin'] = None  # each['origin']
                    dict['to_location'] = config.transfers.id  # 中转库
                    dict['product'] = each['product']
                    dict['from_location'] = data['start']['from_location']
                    dict['invoice_lines'] = ()
                    dict['company'] = 1  # each['company']
                    dict['is_direct_sending'] = each['is_direct_sending']  # 是否直送
                    dict['unit_price'] = each['unit_price']  # 产品的价格
                    dict['lot'] = None
                    dict['starts'] = state
                    dict['uom'] = each['company']
                    dict['real_number'] = each['proposal']  # 产品的请领数量
                    dict['quantity'] = each['proposal']
                    list.append(dict)
                    lv['moves'] = [['create', list]]
                    if len(list_branch) == 5:
                        from_id = data['start']['to_location']
                        if from_id in Keys:
                            start_number = sequence_dict[from_id]
                            start_ = start_number + '20'
                            start_condition_done = 'Y' + start_number + '20'
                        ShipmentNumber = internal.search([('number', 'like', start_ + '%')],
                                                         order=[["create_date", "DESC"]])
                        DoneShipment = internal.search([('number', 'like', start_condition_done + '%')],
                                                       order=[["create_date", "DESC"]])
                        done_number_sequence = DoneShipment[0].number[8:12]
                        done_number = DoneShipment[0].number[2:8]

                        if ShipmentNumber:
                            if int(ShipmentNumber[0].number[1:7]) == int(date):
                                number_sequence = ShipmentNumber[0].number[7:11]
                                if int(done_number) == int(date):
                                    if int(done_number_sequence) > int(number_sequence):
                                        number_int = int(done_number_sequence) + 1
                                        EndNumber = str(number_int).zfill(4)
                                        NumberSequence = start_number + str(date) + str(EndNumber)
                                        lv['number'] = NumberSequence
                                    else:
                                        number_int = int(number_sequence) + 1
                                        EndNumber = str(number_int).zfill(4)
                                        NumberSequence = start_number + str(date) + str(EndNumber)
                                        lv['number'] = NumberSequence
                                else:
                                    number_int = int(number_sequence) + 1
                                    EndNumber = str(number_int).zfill(4)
                                    NumberSequence = start_number + str(date) + str(EndNumber)
                                    lv['number'] = NumberSequence
                            else:
                                NumberSequence = start_number + date + '0001'
                                lv['number'] = NumberSequence
                        elif DoneShipment:
                            if int(DoneShipment[0].number[2:8]) == int(date):
                                number_sequence = DoneShipment[0].number[8:12]
                                if int(done_number) == int(date):
                                    number_int = int(done_number_sequence) + 1
                                    EndNumber = str(number_int).zfill(4)
                                    NumberSequence = start_number + str(date) + str(EndNumber)
                                    lv['number'] = NumberSequence
                                else:
                                    number_int = int(number_sequence) + 1
                                    EndNumber = str(number_int).zfill(4)
                                    NumberSequence = start_number + str(date) + str(EndNumber)
                                    lv['number'] = NumberSequence
                            else:
                                NumberSequence = start_number + date + '0001'
                                lv['number'] = NumberSequence
                        else:
                            NumberSequence = start_number + date + '0001'
                            lv['number'] = NumberSequence
                        internal.create([lv])
                        list_branch[:]
                        list = []
            from_id = data['start']['to_location']
            if from_id in Keys:
                start_number = sequence_dict[from_id]
                start_condition = start_number + str(date)
                start_condition_done = 'Y' + start_number + '20'
            ShipmentNumber = internal.search([('number', 'like', start_condition + '%')],
                                             order=[["create_date", "DESC"]])
            DoneShipment = internal.search([('number', 'like', start_condition_done + '%')],
                                           order=[["create_date", "DESC"]])
            if DoneShipment:
                done_number_sequence = DoneShipment[0].number[8:12]
                done_number = DoneShipment[0].number[2:8]
            else:
                done_number_sequence = 0
                done_number = 0

            if ShipmentNumber:
                if int(ShipmentNumber[0].number[1:7]) == int(date):
                    number_sequence = ShipmentNumber[0].number[7:11]
                    if int(done_number) == int(date):
                        if int(done_number_sequence) > int(number_sequence):
                            number_int = int(done_number_sequence) + 1
                            EndNumber = str(number_int).zfill(4)
                            NumberSequence = start_number + str(date) + str(EndNumber)
                            lv['number'] = NumberSequence
                        else:
                            number_int = int(number_sequence) + 1
                            EndNumber = str(number_int).zfill(4)
                            NumberSequence = start_number + str(date) + str(EndNumber)
                            lv['number'] = NumberSequence
                    else:
                        number_int = int(number_sequence) + 1
                        EndNumber = str(number_int).zfill(4)
                        NumberSequence = start_number + str(date) + str(EndNumber)
                        lv['number'] = NumberSequence
                else:
                    NumberSequence = start_number + date + '0001'
                    lv['number'] = NumberSequence
            elif DoneShipment:
                if int(DoneShipment[0].number[2:8]) == int(date):
                    number_sequence = DoneShipment[0].number[8:12]
                    if int(done_number) == int(date):
                        number_int = int(done_number_sequence) + 1
                        EndNumber = str(number_int).zfill(4)
                        NumberSequence = start_number + str(date) + str(EndNumber)
                        lv['number'] = NumberSequence
                    else:
                        number_int = int(number_sequence) + 1
                        EndNumber = str(number_int).zfill(4)
                        NumberSequence = start_number + str(date) + str(EndNumber)
                        lv['number'] = NumberSequence
                else:
                    NumberSequence = start_number + date + '0001'
                    lv['number'] = NumberSequence
            else:
                NumberSequence = start_number + date + '0001'
                lv['number'] = NumberSequence
            if list == []:
                pass
            else:
                internal.create([lv])
            return action, {}
        else:
            for each in Move:
                if each['is_collar'] == True:
                    ##############################      对内部请领单据的处理（合单）    ##############################
                    interna_query = internal.search([
                        ('straights', '=', True),
                        ('place_of_service', '=', data['start']['to_location']),
                        ('state', '=', 'draft'),
                        ('to_location', '=', config.transfers.id),
                        ('planned_date', '=', data['start']['planned_date']),
                        ('drug_starts', '=', data['start']['starts']),
                    ])
                    Move = Pool().get('stock.move')
                    if interna_query:
                        list_product = []
                        list_move = []
                        move_query = {}
                        for query_each in interna_query:
                            mmm = query_each.moves
                            for i in mmm:
                                if i.change_start == True:
                                    list_product.append(i.product.id)
                                    list_move.append(i.id)
                                    move_query[i.product.id] = [i.id, i.quantity]
                        if each['product'] in list_product:
                            move_id = move_query[each['product']][0]
                            move_quantity = move_query[each['product']][-1]
                            move_line = Move.search([('id', '=', move_id)])
                            quantity = move_quantity + each['proposal']
                            Move.write(move_line, {'quantity': quantity, 'real_number': quantity})
                        else:
                            create_move = Pool().get('stock.move')
                            dict = {}
                            dict['origin'] = None  # each['origin']
                            dict['to_location'] = config.transfers.id  # 中转库
                            dict['product'] = each['product']
                            dict['from_location'] = data['start']['from_location']
                            dict['invoice_lines'] = ()  # each['invoice_lines']
                            dict['company'] = 1  # each['company']
                            dict['is_direct_sending'] = each['is_direct_sending']  # 是否直送
                            dict['unit_price'] = each['unit_price']  # 产品的价格
                            dict['lot'] = None
                            dict['starts'] = state
                            dict['uom'] = each['company']
                            dict['real_number'] = each['proposal']  # 产品的请领数量
                            dict['quantity'] = each['proposal']
                            dict['shipment'] = 'stock.shipment.internal,' + str(interna_query[0].id)
                            create_move.create([dict])
                    else:
                        dict = {}
                        dict['origin'] = None  # each['origin']
                        dict['to_location'] = config.transfers.id  # 中转库
                        dict['product'] = each['product']
                        dict['from_location'] = data['start']['from_location']
                        dict['invoice_lines'] = ()  # each['invoice_lines']
                        dict['company'] = 1  # each['company']
                        dict['is_direct_sending'] = each['is_direct_sending']  # 是否直送
                        dict['unit_price'] = each['unit_price']  # 产品的价格
                        dict['lot'] = None
                        dict['starts'] = state
                        dict['uom'] = each['company']
                        dict['real_number'] = each['proposal']  # 产品的请领数量
                        dict['quantity'] = each['proposal']
                        list_straights.append(dict)
                        lv['straights'] = True
                        from_id = data['start']['to_location']
                        if from_id in Keys:
                            start_number = sequence_dict[from_id]
                            start_ = start_number + str(date)
                            start_condition_done = 'Y' + start_number + '20'
                        ShipmentNumber = internal.search([('number', 'like', start_ + '%')],
                                                         order=[["create_date", "DESC"]])
                        done_list_number = []
                        DoneShipment = internal.search([('number', 'like', start_condition_done + '%')])
                        for i in DoneShipment:
                            done_list_number.append(int(i.number[8:12]))
                        done_list_number.sort()
                        done_number_sequence = done_list_number[-1]

                        if ShipmentNumber:
                            if int(ShipmentNumber[0].number[1:7]) == int(date):
                                number_sequence = ShipmentNumber[0].number[7:11]
                                if int(done_number_sequence) > int(number_sequence):
                                    number_int = int(done_number_sequence) + 1
                                    EndNumber = str(number_int).zfill(4)
                                    NumberSequence = start_number + str(date) + str(EndNumber)
                                    lv['number'] = NumberSequence
                                else:
                                    number_int = int(number_sequence) + 1
                                    EndNumber = str(number_int).zfill(4)
                                    NumberSequence = start_number + str(date) + str(EndNumber)
                                    lv['number'] = NumberSequence
                            else:
                                NumberSequence = start_number + date + '0001'
                                lv['number'] = NumberSequence

                        else:
                            NumberSequence = start_number + date + '0001'
                            lv['number'] = NumberSequence
                        lv['moves'] = [['create', list_straights]]

                    Lines = Pool().get('purchase.line')
                    party_partysd = Pool().get("purchase.purchase")
                    Party = party_partysd.search([
                        ('party', '=', each['party']),
                        ('purchase_date', '=', data['start']['planned_date']),
                        ('delivery_place', '=', data['start']['to_location']),
                        ('state', '=', 'draft'), ])
                    antrag_auf = []
                    Antrag_list = {}
                    lines_dict = {}
                    if Party:
                        product_id = []
                        lines_dicts = {}
                        for lines in Party[0].lines:
                            product_id.append(lines.product.id)
                            lines_dicts[lines.product.id] = lines.id
                        if each['product'] in product_id:
                            product = Pool().get('product.product')
                            product_id = each['product']
                            unit_price = product.search([('id', '=', product_id)])[0].template.cost_price
                            line = Lines.search([('id', '=', lines_dicts[each['product']])])
                            quantity = line[0].quantity + each['proposal']
                            Lines.write(line, {'quantity': quantity, 'unit_price': unit_price})
                        else:
                            sequence_sort = []
                            for lines in Party[0].lines:
                                sequence_sort.append(lines.id)
                            sequence_number = len(sequence_sort) + 1
                            numid = Party[0].id
                            lines_dict['sequence'] = sequence_number  # 序列
                            lines_dict['product'] = each['product']
                            lines_dict['quantity'] = each['proposal']  # 产品请领的数量
                            lines_dict['unit'] = None
                            lines_dict['description'] = ' '  # 产品的描述
                            product = Pool().get('product.product')
                            product_id = each['product']
                            unit_price = product.search([('id', '=', product_id)])[0].template.cost_price
                            lines_dict['unit_price'] = unit_price  # 产品的价格
                            lines_dict['unit'] = each['company']
                            lines_dict['purchase'] = numid
                            lines_dict['drug_starts'] = data['start']['starts']
                            antrag_auf.append(lines_dict)
                            Lines.create(antrag_auf)
                    else:
                        Party = Pool().get('party.party')
                        party = Party.search([
                            ('id', '=', each['party'])
                        ])
                        if party:
                            supplier_payment_term = party[0].supplier_payment_term
                        else:
                            supplier_payment_term = None
                        Antrag_list['party'] = each['party']
                        Antrag_list['invoice_address'] = party[0].addresses[0].id
                        Antrag_list['payment_term'] = supplier_payment_term
                        Antrag_list['company'] = 1
                        Antrag_list['delivery_place'] = data['start']['to_location']  # 送货点
                        Antrag_list['purchase_date'] = data['start']['planned_date']
                        # Antrag_list['warehouse'] = 4  # each['warehouse_location']
                        party_partysd.create([Antrag_list])
                        Party_partysd = party_partysd.search([
                            ('delivery_place', '=', data['start']['to_location']),
                            ('party', '=', each['party']),
                            ('purchase_date', '=', data['start']['planned_date']),
                            ('state', '=', 'draft'),
                        ])
                        sequence_number = 0
                        for each_par in Party_partysd:
                            sequence_number += 1
                            numid = each_par.id
                            lines_dict['sequence'] = sequence_number
                            lines_dict['product'] = each['product']
                            lines_dict['quantity'] = each['proposal']  # 产品请领的数量
                            lines_dict['unit'] = None
                            lines_dict['description'] = ' '  # 产品的描述
                            product = Pool().get('product.product')
                            product_id = each['product']
                            unit_price = product.search([('id', '=', product_id)])[0].template.cost_price
                            lines_dict['unit_price'] = unit_price  # 产品的价格
                            lines_dict['unit'] = each['company']
                            lines_dict['purchase'] = numid
                            lines_dict['drug_starts'] = data['start']['starts']
                            antrag_auf.append(lines_dict)
                            Lines.create(antrag_auf)
        if 'moves' in lv.keys():
            internal.create([lv])
        purchase_id = internal.search([
            ('straights', '=', True),
            ('drug_starts', '=', data['start']['starts']),
            ('state', '=', 'draft'),
            ('to_location', '=', config.transfers.id),
            ('planned_date', '=', data['start']['planned_date']),
        ])
        order_number = purchase_id[0].number
        party_write = Pool().get("purchase.purchase")
        Party = party_write.search([
            ('purchase_date', '=', data['start']['planned_date']),
            ('delivery_place', '=', data['start']['to_location']),
            ('state', '=', 'draft'),
        ])
        for party in Party:
            for i in party.lines:
                if i.drug_starts == data['start']['starts']:
                    line = Lines.search([('id', '=', i.id)])
                    Lines.write(line, {'internal_order': order_number})
                else:
                    pass
        return action, {}


######################    对moves字段的扩充    ################################

class Move:
    __metaclass__ = PoolMeta
    __name__ = "stock.move"

    party = fields.Many2One('party.party', 'party', select=True)  # 科室

    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格

    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格

    starts = fields.Selection([
        ('00', u'常规药品请领单'),
        ('01', u'请退单'),
        ('02', u'非限制转冻结'),
        ('03', u'冻结转非限制'),
        ('04', u'内部调拨'),
        ('05', u' '),
        ('06', u'直送药品请领单'),
    ], 'Starts', select=True)

    outgoing_audit = fields.Selection([
        ('00', u'发药'),
        ('01', u'作废'),
        ('02', u'采购'),
        ('03', u'待发'),
    ], 'utgoing_Audit', select=True)  # 发药处理的状态
    is_direct_sending = fields.Boolean('is_direct_sending', select=True, readonly=True)
    outpatient_7days = fields.Function(fields.Float('Stock Level', select=True), 'get_stock_evel')  # 库存数量
    real_number = fields.Float('Real Number', select=True)  # 请领数量

    reason = fields.Selection([
        ('00', u''),
        ('01', u'药品过期'),
        ('02', u'无外标签'),
        ('03', u'原装破损'),
        ('04', u'科室自用'),
        ('05', u'近期药品'),
        ('06', u'长期不用'),
        ('07', u'停药'),
        ('08', u'病人退药'),
        ('09', u'工作失误'),
        ('10', u'单据错误'),
    ], 'Reason', select=True, states={
        'invisible': Equal(Eval('outgoing_audit'), '02'),
    },
        depends=['outgoing_audit'])  # 退药原因
    comment = fields.Text('Comment', select=True)  # 备注

    move_type = fields.Selection([
        ('000', u''),
        ('101', u'采购订单入库'),
        ('501', u'无采购订单入库'),
        ('452', u'清退出库'),
        ('502', u'无采购订单出库'),
        ('351', u'请领出库'),
        ('352', u'请领入库'),
        ('601', u'临采入库'),
        ('551', u'冻结转非限制'),
        ('252', u'内部调拨入'),
        ('701', u'盘盈'),
        ('Z01', u'医嘱退'),
        ('Z03', u'处方退'),
        ('Z05', u'科室请领退'),
        ('Z07', u'手工消耗退'),
        ('801', u'报溢'),
        ('451', u'请退出库'),
        ('552', u'非限制转冻结'),
        ('251', u'内部调拨出'),
        ('702', u'盘亏'),
        ('Z02', u'医嘱出'),
        ('Z04', u'处方出'),
        ('Z06', u'科室请领出'),
        ('Z08', u'手工消耗出'),
        ('802', u'报损'),
        ('102', u'供应商退货'),
        ('902', u'药库特殊出库'),
    ], 'move_type', select=True)

    check_move = fields.Boolean('check_move')  # 采购修改确认

    change_start = fields.Boolean('change_start')  # 是否合单

    purchase_order = fields.Char('purchase_order', select=True)  # 采购单号

    actual_return = fields.Numeric('actual_return', digits=(16, 4))  # 实退金额

    ######
    @classmethod
    def check_expiration_dates(cls, moves):
        pool = Pool()
        Group = pool.get('res.group')
        User = pool.get('res.user')
        ModelData = pool.get('ir.model.data')

        types = cls.check_expiration_dates_types()
        locations = cls.check_expiration_dates_locations()

        def in_group():
            group = Group(ModelData.get_id('stock_lot_sled',
                                           'group_stock_force_expiration'))
            transition = Transaction()
            user_id = transition.user
            if user_id == 0:
                user_id = transition.context.get('user', user_id)
            if user_id == 0:
                return True
            user = User(user_id)
            return group in user.groups

        for move in moves:
            if not move.to_check_expiration:
                continue
            if (move.from_location.type in types
                or move.to_location.type in types
                or move.from_location in locations
                or move.to_location in locations):
                values = {
                    'move': move.rec_name,
                    'lot': move.lot.rec_name if move.lot else '',
                }
                if not in_group():
                    pass
                    # cls.raise_user_error('expiration_dates', values)
                else:
                    cls.raise_user_warning('%s.check_expiration_dates' % move,
                                           'expiration_dates', values)

    @fields.depends('product')
    def on_change_product(self):
        if self.product:
            Uom = self.product.default_uom
            Retrieve = self.product.is_direct_sending
            hrp = Pool().get('product.product')
            HRP = hrp.search([
                ('id', '=', self.product.id)
            ])
            if HRP:
                self.uom = Uom
                self.is_direct_sending = Retrieve
            else:
                pass

    def get_stock_evel(self, name):
        Date = Pool().get('ir.date')
        Product = Pool().get('product.product')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        with Transaction().set_context(stock_date_end=Date.today()):
            warehouse_quantities = Product.products_by_location([warehouse], [self.product.id], with_childs=True)
            warehouse_quantitie = warehouse_quantities[(warehouse, self.product.id)]
        return warehouse_quantitie

    @staticmethod
    def default_starts():
        return '05'

    @staticmethod
    def default_outgoing_audit():
        return '00'

    @staticmethod
    def default_reason():
        return '00'

    @staticmethod
    def default_move_type():
        return '000'

    @staticmethod
    def default_change_start():
        return True
