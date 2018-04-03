# coding:utf-8
import decimal
import operator
import time
from trytond import config
from trytond.model import ModelView, fields
from trytond.modules.product import Uom
from trytond.pool import Pool
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['InternalRetreat', 'InternalRetreatWizard', 'TestRetreat']


class TestRetreat(ModelView):
    'Test Retreat'
    __name__ = 'hrp_internal_delivery.test_retreat'
    _rec_name = 'number'

    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品名字
    product = fields.Many2One("product.product", "Product", required=True, readonly=True)  # 产品
    from_location = fields.Many2One("stock.location", "from_location", select=True, readonly=True)  # 仓库存储
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    return_quantity = fields.Float('Return Quantity', select=True, readonly=True)  # 请退数量
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)  # 药品批次
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
    ], 'Reason', select=True)  # 退药原因
    comment = fields.Text('Comment', select=True)  # 备注
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    examine = fields.Selection([
        ('00', u''),
        ('01', u'未审核'),
        ('02', u'已审核'),
    ], 'Examine', select=True, readonly=True)  # 退药审核


class InternalRetreat(ModelView):
    'Physique Record'
    __name__ = 'hrp_internal_delivery.internal_retreat'
    _rec_name = 'number'

    effective_date = fields.Date('Effective Date',
                                 states={
                                     'readonly': Eval('state').in_(['cancel', 'done']),
                                 },
                                 depends=['state'])
    planned_date = fields.Date('Planned Date',
                               states={
                                   'readonly': Eval('state') != 'draft',
                               }, depends=['state'], readonly=True)
    actives = fields.Selection([
        ('01', u'请退单'),
    ], 'active', readonly=True)
    moves = fields.One2Many('hrp_internal_delivery.test_retreat', '', 'Moves')
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素')
    ], 'Starts', select=True)  # 药品类型
    message_find = fields.Boolean('message_find', select=True, states={
        'invisible': Equal(Eval('drug_type'), '06')
    }, depends=['drug_type'])  # 查找
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('assigned', 'Assigned'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
    ], 'State', readonly=True)

    @staticmethod
    def default_planned_date():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_drug_type():
        return '06'

    @staticmethod
    def default_actives():
        return '01'

    @fields.depends('drug_type', 'moves', 'message_find')
    def on_change_message_find(self):
        if self.message_find == True:
            if self.drug_type == '06':
                self.moves = []
            else:
                MOVE = Pool().get('hrp_new_product.new_return')
                Product = Pool().get('product.product')
                Lot = Pool().get('stock.lot')
                Date = Pool().get('ir.date')
                list = []
                UserId = Pool().get('hrp_internal_delivery.test_straight')
                from_location_id = UserId.get_user_id()
                mmm = MOVE.search([
                    ('examine', '=', '02'),
                    ('from_location', '=', from_location_id),
                    ('drug_type', '=', self.drug_type),
                ])
                for each in mmm:
                    # context = ({'stock_date_end': Date.today(), 'forecast': True})
                    # with Transaction().set_context(context=context):
                    #     warehouse_quant = Product.products_by_location([each.to_location.id],
                    #                                                    [each.product.id],
                    #                                                    with_childs=False,
                    #                                                    grouping=('product', 'lot'))#预测数量
                    dict = {}
                    with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([each.to_location.id],
                                                                       [each.product.id],
                                                                       with_childs=False,
                                                                       grouping=('product', 'lot'))
                        lists = []
                        done_list = []
                        for key, value in warehouse_quant.items():
                            if value > 0.0:
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
                        num = 0
                        number = 0
                        quantity = each.can_return_quantity
                        for id_lot in range(len_lot):
                            lot_quant = warehouse_quant[(
                                each.to_location.id, each.product.id, done_list[id_lot])]  # 对应批次的库存数量
                            if number >= quantity:
                                break
                            else:
                                num += 1
                                number += lot_quant
                        for lo in range(num):
                            if num == 1:
                                dict_one = {}
                                dict_one['lot'] = done_list[lo]
                                dict_one['from_location'] = each.from_location.id
                                dict_one['to_location'] = each.to_location.id
                                dict_one['product'] = each.product.id
                                dict_one['product_name'] = each.product.name
                                dict_one['code'] = each.code
                                dict_one['drug_specifications'] = each.drug_specifications
                                dict_one['uom'] = each.uom.id
                                dict_one['return_quantity'] = quantity
                                dict_one['is_collar'] = True
                                dict_one['is_direct_sending'] = each.is_direct_sending
                                dict_one['examine'] = each.examine
                                dict_one['reason'] = each.reason
                                list.append(dict_one)

                            else:
                                if lo == 0:
                                    lot_quant_one = warehouse_quant[
                                        (each.to_location.id, each.product.id, done_list[lo])]
                                    dict_two = {}
                                    dict_two['lot'] = done_list[lo]
                                    dict_two['from_location'] = each.from_location.id
                                    dict_two['to_location'] = each.to_location.id
                                    dict_two['product'] = each.product.id
                                    dict_two['product_name'] = each.product.name
                                    dict_two['code'] = each.code
                                    dict_two['drug_specifications'] = each.drug_specifications
                                    dict_two['uom'] = each.uom.id
                                    dict_two['return_quantity'] = lot_quant_one
                                    dict_two['is_collar'] = True
                                    dict_two['is_direct_sending'] = each.is_direct_sending
                                    dict_two['examine'] = each.examine
                                    dict_two['reason'] = each.reason
                                    list.append(dict)

                                elif lo == num - 1:
                                    lot_quant_two = warehouse_quant[
                                        (each.to_location.id, each.product.id, done_list[lo])]
                                    Quantity = lot_quant_two - (number - quantity)
                                    dict['lot'] = done_list[lo]
                                    dict['from_location'] = each.from_location.id
                                    dict['to_location'] = each.to_location.id
                                    dict['product'] = each.product.id
                                    dict['product_name'] = each.product.name
                                    dict['code'] = each.code
                                    dict['drug_specifications'] = each.drug_specifications
                                    dict['uom'] = each.uom.id
                                    dict['return_quantity'] = Quantity
                                    dict['is_collar'] = True
                                    dict['is_direct_sending'] = each.is_direct_sending
                                    dict['examine'] = each.examine
                                    dict['reason'] = each.reason
                                    list.append(dict_two)
                                else:
                                    lot_quant_three = warehouse_quant[
                                        (each.to_location.id, each.product.id, done_list[lo])]
                                    dict_three = {}
                                    dict_three['lot'] = done_list[lo]
                                    dict_three['from_location'] = each.from_location.id
                                    dict_three['to_location'] = each.to_location.id
                                    dict_three['product'] = each.product.id
                                    dict_three['product_name'] = each.product.name
                                    dict_three['code'] = each.code
                                    dict_three['drug_specifications'] = each.drug_specifications
                                    dict_three['uom'] = each.uom.id
                                    dict_three['return_quantity'] = lot_quant_three
                                    dict_three['is_collar'] = True
                                    dict_three['is_direct_sending'] = each.is_direct_sending
                                    dict_three['examine'] = each.examine
                                    dict_three['reason'] = each.reason
                                    list.append(dict_three)
                self.moves = list
        else:
            self.moves = []

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
        return super(InternalRetreat, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        # Cancel before delete
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalRetreat, cls).delete(shipments)


class InternalRetreatWizard(Wizard):
    __name__ = 'hrp_internal_delivery.internal_retreat_wizard'

    start = StateView('hrp_internal_delivery.internal_retreat',
                      'hrp_internal_delivery.internal_retreat_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_internal_retreat')

    def do_create_(self, action):
        Date = Pool().get('ir.date')
        today = Date.today()
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        to_location_id = UserId.get_user_id()

        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        internal = Pool().get('stock.shipment.internal')
        new_return = Pool().get('hrp_new_product.new_return')
        Product = Pool().get('product.product')
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        lv = {}
        Move = data['start']['moves']
        MOVE = Pool().get('hrp_new_product.new_return')
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        from_location_id = UserId.get_user_id()
        list_now = []
        scrap = [('examine', '=', '02'),
                 ('from_location', '=', from_location_id),
                 ]
        if data['start']['drug_type'] == '06':
            pass
        else:
            scrap.append(('drug_type', '=', data['start']['drug_type']))
        mmm = MOVE.search(scrap)
        for i in mmm:
            dict = {}
            dict['product'] = i.product.id
            dict['return_quantity'] = i.can_return_quantity
            list_now.append(dict)
        now_data = sorted(list_now, key=lambda x: (x['product'], x['return_quantity']), reverse=False)
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        list_compare = []
        for each in Move:
            dict = {}
            dict['product'] = each['product']
            dict['return_quantity'] = each['return_quantity']
            list_compare.append(dict)
        # list_compare = UserId.get_default_moves_now()
        before_data = sorted(list_compare, key=lambda x: (x['product'], x['return_quantity']), reverse=False)

        product_id = []
        for each in before_data:
            product_id.append(each['product'])
        a = {}
        for p_id in product_id:
            if product_id.count(p_id) > 1:
                a[p_id] = product_id.count(p_id)
        key_value = a.keys()
        productid = []
        now_list = []
        for each_ in before_data:
            if each_['product'] in key_value:
                dict = {}
                dict[each_['product']] = each_['return_quantity']
                productid.append(dict)
                now_list.append(each_)
        expected = [l for l in before_data if l not in now_list]
        for pro in key_value:
            number = 0
            dict_ = {}
            for i in productid:
                try:
                    number += i[pro]
                except:
                    pass
            dict_['product'] = pro
            dict_['return_quantity'] = number
            expected.append(dict_)
        expected_data = sorted(expected, key=lambda x: (x['product'], x['return_quantity']), reverse=False)
        if expected_data == now_data:
            list = []
            for each in Move:
                get_apply_number = UserId.get_apply_number(to_location_id)
                lv['number'] = get_apply_number
                lv['starts'] = '01'
                lv['to_location'] = config.transfers.id  # 中转库存地
                lv['from_location'] = each['to_location']
                lv['company'] = 1  # data['start']['company']
                lv['state'] = data['start']['state']
                lv['place_of_service'] = config.return_of.id  # 到达库存地(中心药库冻结区)
                lv['drug_starts'] = data['start']['drug_type']
                dict = {}
                if each['reason'] == '00':
                    pass
                else:
                    dict['origin'] = None
                    dict['starts'] = data['start']['actives']
                    dict['product'] = each['product']
                    dict['planned_date'] = data['start']['planned_date']
                    dict['from_location'] = each['to_location']
                    dict['to_location'] = config.transfers.id  # 中转库存地
                    dict['is_direct_sending'] = each['is_direct_sending']
                    dict['company'] = 1
                    dict['reason'] = each['reason']
                    dict['comment'] = each['comment']
                    dict['invoice_lines'] = ()
                    dict['unit_price'] = None  # each['unit_price']
                    dict['lot'] = each['lot']
                    dict['uom'] = each['uom']
                    dict['quantity'] = each['return_quantity']
                    dict['real_number'] = each['return_quantity']
                    with Transaction().set_context(stock_date_end=today, stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([each['to_location']],
                                                                       [each['product']], [each['lot']],
                                                                       grouping=('product', 'lot'))
                        for key, value in warehouse_quant.items():
                            if value > each['return_quantity']:
                                pass
                            else:
                                return self.raise_user_error(u'%s,数量不满足,请联系采购确认可退数量', each['product_name'])
                    cost_prices = Product.search([('id', '=', each['product'])])[0].cost_price
                    list_prices = Product.search([('id', '=', each['product'])])[0].list_price

                    list_ = decimal.Decimal(
                        str(float(list_prices * decimal.Decimal(str(each['return_quantity'])))))  # 批发总价
                    cost_ = decimal.Decimal(
                        str(float(cost_prices * decimal.Decimal(str(each['return_quantity'])))))  # 零售总价

                    list_price = decimal.Decimal(-list_).quantize(decimal.Decimal('0.00'))
                    cost_price = decimal.Decimal(-cost_).quantize(decimal.Decimal('0.00'))
                    dict['list_price'] = list_price
                    dict['cost_price'] = cost_price
                    list.append(dict)
                    lv['moves'] = [['create', list]]
                    NewReturn = new_return.search([
                        ('product', '=', each['product']),
                        ('from_location', '=', each['from_location']),
                    ])
                    if NewReturn:
                        write_dict = {}
                        write_dict['examine'] = '01'
                        write_dict['can_return_quantity'] = None
                        new_return.write(NewReturn, write_dict)
        else:
            return self.raise_user_error(u'数据有所更新，请您退出该界面重新进行操作')
        internal.create([lv])

        Internal = internal.search([
            ('from_location', '=', data['start']['moves'][0]['to_location'])
        ])
        internal.wait(Internal)
        internal.assign(Internal)
        internal.done(Internal)
        return action, {}
