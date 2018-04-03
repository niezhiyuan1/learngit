# coding:utf-8
import operator
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Equal
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.wizard import StateReport
from trytond.wizard import Wizard, StateView, Button
import sys
reload(sys)
sys.setdefaultencoding('utf8')

__all__ = ['InternalCoreDrug', 'InternalCoreDrugWizard', 'CoreDrugReport']


class InternalCoreDrug(ModelView):
    """InternalRelieve"""
    __name__ = 'hrp_internal_delivery.internal_core_drug'

    starts = fields.Selection([
        ('00', u'常规药品请领单'),
        ('01', u'请退单'),
    ], 'Starts', select=True)  # 移动类型
    state = fields.Selection([
        ('draft', u'请领发药'),
        ('01', u'请退收药'),
    ], 'State', select=True, readonly=False)  # 状态
    drug_starts = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u''),
        ('07', u'同位素'),
    ], 'drug_starts', select=True, states={
        'invisible': Equal(Eval('starts'), '02') | Equal(Eval('starts'), '03')
    }, depends=['starts'])
    number = fields.Char('number', select=True)  # 单号
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    message_find = fields.Boolean('Find', select=True, states={
        'invisible': Equal(Eval('starts'), '00') & Equal(Eval('drug_starts'), '06') | Equal(Eval('starts'),
                                                                                            '01') & Equal(
            Eval('drug_starts'), '06') | Equal(Eval('starts'), '06') & Equal(Eval('drug_starts'), '06')
    }, depends=['drug_starts', 'starts'])  # 查找按钮

    department = fields.Selection([
        ('00', u''),
        ('01', u'住院药房'),
        ('02', u'门诊药房'),
        ('03', u'制剂室'),
        ('04', u'体检药房'),
        ('05', u'内镜药房'),
        ('06', u'放射科'),
        ('07', u'草药房'),
    ], 'department', select=True, states={
        'invisible': Equal(Eval('starts'), '02') | Equal(Eval('starts'), '03')
    }, depends=['starts'])  # 选择部门

    moves = fields.One2Many('hrp_internal_delivery.internal_move_list', 'None', 'Moves')

    @staticmethod
    def default_drug_starts():
        return '06'

    @staticmethod
    def default_starts():
        return '00'

    @staticmethod
    def default_state():
        return 'draft'

    @fields.depends('starts', 'state')
    def on_change_starts(self):
        if self.starts == '00':
            self.state = 'draft'
        if self.starts == '01':
            self.state = '01'

    @staticmethod
    def default_department():
        return '00'

    @staticmethod
    def default_to_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @fields.depends('state', 'starts')
    def on_change_starts(self):
        if self.starts == '00':
            self.state = 'draft'
        if self.starts == '01':
            self.state = '01'
        else:
            pass

    @fields.depends('starts', 'moves', 'state', 'to_location', 'message_find', 'drug_starts', 'number', 'department')
    def on_change_message_find(self):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        if self.message_find == True:
            if self.department == '01':  # 住院药房
                department_id = config.hospital.storage_location.id
                department_frozen_id = config.hospital_freeze.id  # 住院药房冻结区
            if self.department == '02':  # 门诊药房
                department_id = config.outpatient_service.storage_location.id
                department_frozen_id = config.outpatient_freeze.id  # 门诊冻结区
            if self.department == '03':  # 制剂室
                department_id = config.preparation.storage_location.id
                department_frozen_id = config.outpatient_freeze.id  # 制剂室冻结区
            if self.department == '04':  # 体检药房
                department_id = config.medical.storage_location.id
                department_frozen_id = config.medical.freeze_location.id  # 体检药房冻结区
            if self.department == '05':  # 内镜药房
                department_id = config.endoscopic.storage_location.id
                department_frozen_id = config.endoscopic.freeze_location.id  # 内镜药房冻结区
            if self.department == '06':  # 放射科
                department_id = config.ward.storage_location.id
                department_frozen_id = config.ward.freeze_location.id  # 放射科冻结区
            if self.department == '07':  # 草药房
                department_id = config.herbs.storage_location.id
                department_frozen_id = config.herbs.freeze_location.id  # 草药房冻结区
            if self.to_location.id == config.warehouse.storage_location.id:  # 默认1级药房
                Product = Pool().get('product.product')
                Date = Pool().get('ir.date')
                internal = Pool().get('stock.shipment.internal')
                if self.starts == '01':  # 判断是否为请退
                    if self.state == 'draft':
                        TestInternal = []
                    elif self.state == '01':
                        if self.department == '00':
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('drug_starts', '=', self.drug_starts),
                                    ('state', '=', 'draft'),
                                    ('starts', '=', self.starts),
                                    ('to_location', '=', config.return_of.id),  # 查找到达一级库冻结区的订单
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', 'draft'),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                        else:
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('state', '=', 'draft'),
                                    ('starts', '=', self.starts),
                                    ('drug_starts', '=', self.drug_starts),
                                    ('to_location', '=', config.return_of.id),  # 查找到达一级库冻结区的订单
                                    ('place_of_service', '=', department_frozen_id),
                                    ('from_location', '=', config.transfers.id),  # 查找到达一级库冻结区的订单
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', 'draft'),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                    else:
                        if self.department == '00':
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('drug_starts', '=', self.drug_starts),
                                    ('to_location', '=', config.return_of.id),  # 查找到达一级库冻结区的订单
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                        else:
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('drug_starts', '=', self.drug_starts),
                                    ('to_location', '=', config.return_of.id),  # 查找到达一级库冻结区的订单
                                    ('place_of_service', '=', department_frozen_id),  # 查找到达一级库冻结区的订单
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                elif self.starts == '02':  # 判断是否为冻结/非限制
                    if self.number == '':
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('from_location', '=', config.warehouse.storage_location.id),
                        ])
                    else:
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('number', '=', self.number),
                            ('straights', '=', False),
                            ('drug_starts', '=', self.drug_starts),
                        ])
                elif self.starts == '03':  # 判断是否为冻结/非限制
                    if self.number == '':
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('to_location', '=', config.warehouse.storage_location.id), ])
                    else:
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('number', '=', self.number),
                            ('straights', '=', False),
                            ('drug_starts', '=', self.drug_starts),
                        ])
                else:
                    if self.state == '01':
                        TestInternal = []
                    else:
                        if self.department == '00':
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('straights', '=', False),
                                    ('from_location', '=', config.warehouse.storage_location.id),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                        else:
                            if self.number == '':
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('straights', '=', False),
                                    ('place_of_service', '=', department_id),
                                    ('from_location', '=', config.warehouse.storage_location.id),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                            else:
                                TestInternal = internal.search([
                                    ('state', '=', self.state),
                                    ('starts', '=', self.starts),
                                    ('number', '=', self.number),
                                    ('straights', '=', False),
                                    ('drug_starts', '=', self.drug_starts),
                                ])
                if TestInternal:
                    test_list = []
                    for i in TestInternal:
                        Shipment_id = i.id
                        lv = {}
                        list = []
                        if self.state == '01':
                            lv['state'] = 'draft'
                        else:
                            lv['state'] = self.state
                        lv['move_number'] = str(i.number)
                        lv['shipment_id'] = Shipment_id
                        if self.starts == '06':
                            lv['starts'] = '00'
                        if self.starts == '02':
                            lv['starts'] = '03'
                        else:
                            lv['starts'] = self.starts
                        lv['location'] = i.place_of_service
                        lv['move_time'] = i.planned_date
                        lv['from_location'] = i.from_location
                        lv['to_location'] = i.to_location
                        lv['place_of_service'] = i.place_of_service
                        lv['drug_starts'] = i.drug_starts  # 药品类型
                        Move = i.moves
                        for each in Move:
                            move_id = each.id
                            dict = {}
                            dict['product'] = each.product.name
                            locals = each.from_location
                            with Transaction().set_context(stock_date_end=Date.today()):
                                quantities = Product.products_by_location([locals], [each.product.id], with_childs=True)
                            if quantities.values():
                                stock_level = [v for v in quantities.values()][0]
                            else:
                                stock_level = 0
                            dict['stock_level'] = str(stock_level)
                            dict['move_id'] = move_id  # 每条数据的id
                            if each.product.a_charge == None:
                                dict['a_charge'] = ''
                            else:
                                dict['a_charge'] = str(each.product.a_charge)
                            dict['outgoing_audit'] = each.outgoing_audit
                            if each.product.template.drug_specifications == None:
                                dict['drug_specifications'] = ''
                            else:
                                dict['drug_specifications'] = each.product.template.drug_specifications
                            dict['code'] = str(each.product.code)
                            dict['company'] = each.uom.id
                            dict['uom'] = each.uom.id
                            dict['odd_numbers'] = each.real_number
                            dict['is_direct_sending'] = each.is_direct_sending
                            dict['proposal'] = each.quantity
                            dict['return_quantity'] = each.real_number
                            if stock_level < each.quantity:
                                dict['prompt'] = '01'
                            else:
                                pass
                            dict['reason'] = each.reason  # 退药原因
                            dict['comment'] = each.comment  # 退药备注
                            dict['lot'] = each.lot  # 退药的批次
                            if each.lot != None:
                                dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                            else:
                                pass
                            list.append(dict)
                        if self.starts == '00':  # 请领单
                            lv['move_apply'] = sorted(list, key=operator.itemgetter('product'))
                        if self.starts == '01':  # 请退单
                            lv['move_return'] = sorted(list, key=operator.itemgetter('product'))
                        if self.starts == '06':  # 直送药品请领单
                            lv['move_apply'] = sorted(list, key=operator.itemgetter('product'))
                        if self.starts == '03':  # 冻结/非限制
                            lv['move_frozen'] = sorted(list, key=operator.itemgetter('product'))
                        if self.starts == '02':  # 非限制/冻结
                            lv['move_frozen'] = sorted(list, key=operator.itemgetter('product'))
                        test_list.append(lv)
                        test_list.sort(key=lambda x: x['move_time'], reverse=True)
                    self.moves = test_list
                else:
                    pass

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_actives():
        return '04'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class InternalCoreDrugWizard(Wizard):
    __name__ = 'hrp_internal_delivery.internal_core_drug_wizard'

    start = StateView('hrp_internal_delivery.internal_core_drug',
                      'hrp_internal_delivery.internal_core_drug_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'print_', 'tryton-ok', default=True),
                      ])





    print_ = StateReport('hrp_internal_delivery.core_drug_report')





    def do_print_(self, action):
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        Move = data['start']['moves']
        for each in Move:
            if each['message_confirm'] == True:
                if each['starts'] == '00':
                    move_apply = each['move_apply']
                    for i in move_apply:
                        Moves = Pool().get('stock.move')
                        move_id = i['move_id']
                        move_line = Moves.search([('id', '=', move_id)])
                        if move_line:
                            dict = {}
                            dict['quantity'] = i['proposal']
                            if i['outgoing_audit'] == '00' and float(i['stock_level']) < float(i['proposal']):
                                return self.raise_user_error(u'药品请领单数量大于当前库存数')
                            if i['outgoing_audit']:
                                dict['outgoing_audit'] = i['outgoing_audit']
                            else:
                                dict['outgoing_audit'] = '00'
                            Moves.write(move_line, dict)
                        else:
                            self.raise_user_error(u'该请领单已经修改,请重新进行处理')
                if each['starts'] == '01':  # 中心请退
                    move_return = each['move_return']
                    for i in move_return:
                        Moves = Pool().get('stock.move')
                        move_id = i['move_id']
                        ddd = Moves.search([('id', '=', move_id)])
                        dict = {}
                        dict['quantity'] = i['return_quantity']
                        Moves.write(ddd, dict)

                if each['starts'] == '02' or '03':  # 冻结/非限制
                    move_frozen = each['move_frozen']
                    for i in move_frozen:
                        Moves = Pool().get('stock.move')
                        move_id = i['move_id']
                        ddd = Moves.search([('id', '=', move_id)])
                        dict = {}
                        dict['quantity'] = i['proposal']
                        Moves.write(ddd, dict)

                if each['starts'] == '04':  # 内部移动
                    move_straight = each['move_straight']
                    internal = Pool().get('stock.shipment.internal')
                    Date = Pool().get('ir.date')
                    today = Date.today()
                    lv = {}
                    lv['starts'] = data['start']['starts']
                    lv['company'] = 1
                    lv['to_location'] = data['start']['moves'][0]['to_location']  # 中转库存地transfers
                    lv['from_location'] = data['start']['moves'][0]['from_location']
                    lv['place_of_service'] = data['start']['moves'][0]['place_of_service']
                    lv['state'] = u'draft'
                    lv['planned_date'] = today
                    lv['number'] = data['start']['moves'][0]['move_number']
                    list_dict = []
                    for i in move_straight:
                        if i['storage'] == True:
                            Moves = Pool().get('stock.move')
                            move_id = i['move_id']
                            ddd = Moves.search([('id', '=', move_id)])
                            dict = {}
                            dict['quantity'] = i['proposal']
                            Moves.write(ddd, dict)
                        else:
                            Moves = Pool().get('stock.move')
                            move_id = i['move_id']
                            ddd = Moves.search([('id', '=', move_id)])
                            Moves.delete(ddd)
                            dict = {}
                            dict['origin'] = None  # each['origin']
                            product_name = i['product']
                            product = Pool().get('product.product')
                            product_id = product.search([('name', '=', product_name)])
                            ProductId = product_id[0].id
                            dict['product'] = ProductId
                            dict['from_location'] = data['start']['moves'][0]['from_location']
                            dict['to_location'] = data['start']['moves'][0]['to_location']
                            dict['lot'] = i['lot']
                            dict['starts'] = data['start']['starts']
                            dict['uom'] = i['uom']
                            dict['real_number'] = i['proposal']  # 产品的请领数量
                            dict['quantity'] = i['proposal']
                            list_dict.append(dict)
                            lv['moves'] = [['create', list_dict]]
                    if 'moves' in lv.keys():
                        internal.create([lv])

                if each['starts'] == '05':  # 二级请退
                    move_return_two = each['move_return_two']
                    for i in move_return_two:
                        Moves = Pool().get('stock.move')
                        move_id = i['move_id']
                        ddd = Moves.search([('id', '=', move_id)])
                        dict = {}
                        dict['quantity'] = i['return_quantity']
                        Moves.write(ddd, dict)

                if each['starts'] == '06':  # 二级药库请领
                    move_look_two = each['move_look_two']
                    internal = Pool().get('stock.shipment.internal')
                    Date = Pool().get('ir.date')
                    today = Date.today()
                    lv = {}
                    lv['starts'] = data['start']['starts']
                    lv['company'] = 1
                    lv['to_location'] = data['start']['moves'][0]['to_location']  # 中转库存地transfers
                    lv['from_location'] = data['start']['moves'][0]['from_location']
                    lv['place_of_service'] = data['start']['moves'][0]['place_of_service']
                    lv['state'] = u'draft'
                    lv['planned_date'] = today
                    lv['number'] = data['start']['moves'][0]['move_number']
                    if data['start']['starts'] == '06':
                        lv['straights'] = True
                    else:
                        pass
                    lv['drug_starts'] = data['start']['drug_starts']
                    list_dict = []
                    for i in move_look_two:
                        if i['storage'] == True:
                            Moves = Pool().get('stock.move')
                            move_id = i['move_id']
                            ddd = Moves.search([('id', '=', move_id)])
                            dict = {}
                            dict['quantity'] = i['proposal']
                            Moves.write(ddd, dict)
                        else:
                            Moves = Pool().get('stock.move')
                            move_id = i['move_id']
                            ddd = Moves.search([('id', '=', move_id)])
                            Moves.delete(ddd)
                            dict = {}
                            dict['origin'] = None  # each['origin']
                            product_name = i['product']
                            product = Pool().get('product.product')
                            product_id = product.search([('name', '=', product_name)])
                            ProductId = product_id[0].id
                            dict['product'] = ProductId
                            dict['from_location'] = data['start']['moves'][0]['from_location']
                            dict['to_location'] = data['start']['moves'][0]['to_location']
                            dict['invoice_lines'] = ()  # each['invoice_lines']
                            dict['company'] = 1  # each['company']
                            dict['is_direct_sending'] = i['is_direct_sending']  # 是否直送
                            dict['lot'] = i['lot']
                            dict['starts'] = data['start']['starts']
                            dict['uom'] = i['company']
                            dict['real_number'] = i['proposal']  # 产品的请领数量
                            dict['quantity'] = i['proposal']
                            dict['a_charge'] = i['a_charge']
                            list_dict.append(dict)
                            lv['moves'] = [['create', list_dict]]
                    if 'moves' in lv.keys():
                        internal.create([lv])

        for move in data['start']['moves']:
            if move['message_confirm'] == True:
                move_number = move['move_number']
                shipment_id = move['shipment_id']
                internal = Pool().get('stock.shipment.internal')
                Internal = internal.search([
                    ('number', '=', move_number),
                    ('id', '=', shipment_id),
                ])
                internal.wait(Internal)
                internal.assign(Internal)
                internal.done(Internal)
            else:
                pass
        # return action, data


class CoreDrugReport(Report):
    __name__ = 'hrp_internal_delivery.core_drug_report'

    @classmethod
    def _get_records(cls, ids, model, data):
        Location = Pool().get('stock.location')
        Internal = Pool().get('stock.shipment.internal')
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        location_one = config.warehouse.storage_location.id
        move_number = []
        for each in data['start']['moves']:
            if each['message_confirm'] == True:
                move_number.append(each['move_number'])
        # clause = [
        #             ('number', '=','Y'+move_number[0]),
        #             ('state', '=', 'done'),
        #             ('from_location', '=',location_one),
        #         ]
        # return Internal.search(clause,order=[ ('id', 'ASC')])
        #
        internal = Internal.search([('number', '=', 'Y' + move_number[0]),
                                    ('state', '=', 'done'),
                                    ('from_location', '=', location_one),  # location_one
                                    ])
        data_dict = {}
        for i in internal:
            location = Location.search([('id', '=', i.place_of_service.id)])[0].name
            data_dict['to_location'] = location
            data_dict['move_time'] = i.effective_date
            data_dict['number'] = 'Y' + move_number[0]
            move_list = []
            for move_each in i.moves:
                move_dict = {}
                move_dict['code'] = move_each.product.code
                move_dict['list_price'] = move_each.list_price
                move_dict['product'] = move_each.product.name
                if move_each.lot == None:
                    move_dict['lot'] = ''
                    move_dict['shelf_life_expiration_date'] = ''
                else:
                    move_dict['lot'] = move_each.lot.number
                    move_dict['shelf_life_expiration_date'] = move_each.lot.shelf_life_expiration_date
                move_dict['quantity'] = move_each.quantity
                move_dict['uom'] = move_each.uom.name
                move_dict['attach'] = move_each.product.template.attach
                move_dict['drug_specifications'] = move_each.product.template.drug_specifications
                move_list.append(move_dict)
            data_dict['moves'] = move_list
        return [data_dict]

    @classmethod
    def get_context(cls, records, data):
        super(CoreDrugReport, cls).get_context(records, {})
        report_context = super(CoreDrugReport, cls).get_context(records, data)
        return report_context
