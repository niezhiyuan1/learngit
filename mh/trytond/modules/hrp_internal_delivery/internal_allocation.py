# coding:utf-8
import operator
from trytond.model import ModelView, fields
from trytond.modules.product import Uom
from trytond.pool import Pool
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['InternalAllocation', 'InternalAllocationWizard', 'InternalMoveList', 'ApplyMoveLook', 'ApplyMoveLookTwo',
           'ReturnMoveLook', 'ReturnMoveLookTwo', 'StraightMoveLook', 'FrozenMoveLook']


###############################    内部调拨筛选    ####################################

class InternalMoveList(ModelView):
    """Internal MoveList"""

    __name__ = 'hrp_internal_delivery.internal_move_list'
    _rec_name = 'number'

    # done_time = fields.Date('Done Time',select=True) #

    move_time = fields.Date('move_time', select=True, readonly=True)  # 时间
    move_number = fields.Char('Number', select=True, readonly=True)  # 单号
    shipment_id = fields.Char('shipment_id', select=True)  # shipment_id
    location = fields.Many2One("stock.location", "location", select=True)  # 创建的部门
    from_location = fields.Many2One("stock.location", "from_location", select=True, readonly=True)  # 来自库存地
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 到达库存地
    place_of_service = fields.Many2One("stock.location", "place_of_service", select=True, readonly=True)  # 中转库存地
    message_confirm = fields.Boolean('confirm', select=True, states={
        'invisible': Equal(Eval('state'), 'done') | Equal(Eval('state'), '01') | Equal(Eval('state'), '04') | Equal(
            Eval('state'), '05')
    })  # 确认
    starts = fields.Selection([
        ('00', u'一级请领单'),
        ('01', u'请退单'),
        ('02', u'二级请退单'),
        ('03', u'冻结转非限制'),
        ('04', u'内部调拨'),
        ('05', u'二级请退'),
        ('06', u'二级药库请领单'),
    ], 'Starts', select=True)

    state = fields.Selection([
        ('draft', u'起草'),
        ('assigned', u'分配'),
        ('waiting', u'等待'),
        ('done', u'完成'),
        ('01', u'完成 '),
        ('04', u'完成  '),
        ('005', u'完成3'),
    ], 'State', select=True, readonly=True)
    move_apply = fields.One2Many('hrp_internal_delivery.apply_move_look', '', 'move_apply',
                                 states={
                                     'invisible': ~Equal(Eval('starts'), '00')
                                 }, depends=['starts'])  # 中心药库请领
    move_look_two = fields.One2Many('hrp_internal_delivery.apply_move_look_two', '', 'move_look_two',
                                    states={
                                        'invisible': ~Equal(Eval('starts'), '06')
                                    }, depends=['starts'])  # 二级药库请领
    move_return = fields.One2Many('hrp_internal_delivery.return_move_look', '', 'move_return',
                                  states={
                                      'invisible': ~Equal(Eval('starts'), '01')
                                  }, depends=['starts'])  # 中心请退
    move_return_two = fields.One2Many('hrp_internal_delivery.return_move_look_two', '', 'move_return_two',
                                      states={
                                          'invisible': ~Equal(Eval('starts'), '05')
                                      }, depends=['starts'])  # 二级请退
    move_straight = fields.One2Many('hrp_internal_delivery.straight_move_look', '', 'move_straight',
                                    states={
                                        'invisible': ~Equal(Eval('starts'), '04')
                                    }, depends=['starts'])  # 内部调拨
    move_frozen = fields.One2Many('hrp_internal_delivery.frozen_move_look', '', 'move_frozen',
                                  states={
                                      'invisible': ~Equal(Eval('starts'), '03')
                                  }, depends=['starts'])  # 冻结/非限制


###################################  中心药库 请领单界面   ######################################
class ApplyMoveLook(ModelView):
    """ApplyMoveLook"""
    __name__ = 'hrp_internal_delivery.apply_move_look'

    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    code = fields.Char('code', select=True, readonly=True)  # 药品编码
    company = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    lot = fields.Many2One('stock.lot', 'lot', select=True, readonly=True)
    odd_numbers = fields.Float('odd_numbers', select=True, readonly=True)  # 建议请领数量
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Char('stock_level', select=True, readonly=True)  # 现有库存量
    outpatient_7days = fields.Float('Outpatient_7days', select=True, readonly=True)  # 7日量
    proposal = fields.Float('proposal', select=True, readonly=False, states={'readonly': ~Eval('is_collar', True),
                                                                             })  # 请领数量
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    party = fields.Many2One('party.party', 'Party', select=True)  # 供应商
    unit_price = fields.Numeric('unit_price')  # 价格
    outgoing_audit = fields.Selection([
        ('00', u'发药'),
        ('01', u'作废'),
        ('03', u'待发'),
    ], 'utgoing_Audit', select=True)  # 发药处理的状态

    state = fields.Selection([
        ('draft', u'起草'),
        ('waiting', u'等待'),
        ('done', u'完成'),
    ], 'State', select=True, readonly=False)  # 状态

    prompt = fields.Selection([
        ('00', u''),
        ('01', u'库存不足'),
    ], 'prompt', select=True, readonly=True)  # 提示

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_prompt():
        return '00'


##########################     二级库房 请领单界面    #######################################
class ApplyMoveLookTwo(ModelView):
    """ApplyMoveLookTwo"""
    __name__ = 'hrp_internal_delivery.apply_move_look_two'

    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    company = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    odd_numbers = fields.Float('odd_numbers', select=True, readonly=True)  # 建议请领数量
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Char('stock_level', select=True, readonly=True)  # 现有库存量
    outpatient_7days = fields.Float('Outpatient_7days', select=True, readonly=True)  # 7日量
    proposal = fields.Float('proposal', select=True, readonly=True)  # 请领数量
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    is_collar = fields.Boolean('is_collar', select=True)  # 是否请领
    party = fields.Many2One('party.party', 'Party', select=True)  # 供应商
    unit_price = fields.Numeric('unit_price')  # 价格
    lot = fields.Many2One('stock.lot', 'lot', select=True, readonly=True)  # 批次
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', select=True, readonly=True)  # 有效时间
    storage = fields.Boolean('storage', select=True)  # 入库确认

    @staticmethod
    def default_storage():
        return True


###############   中心请退单界面   #####################
class ReturnMoveLook(ModelView):
    """ReturnMoveLook"""
    __name__ = 'hrp_internal_delivery.return_move_look'

    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    from_location = fields.Many2One("stock.location", "from_location", select=True, readonly=True)  # 仓库存储
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    return_quantity = fields.Integer('Return Quantity', select=True, readonly=True)  # 请退数量
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)  # 药品批次
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', select=True, readonly=True)  # 有效时间
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
        ('3', u'单据错误'),
    ], 'Reason', select=True, readonly=True)  # 退药原因
    comment = fields.Text('Comment', select=True)  # 备注
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    examine = fields.Selection([
        ('00', u''),
        ('01', u'未审核'),
        ('02', u'已审核'),
    ], 'Examine', select=True, readonly=True)  # 退药审核


###############     二级药库请退单界面    #####################
class ReturnMoveLookTwo(ModelView):
    """Return Move Look Two"""
    __name__ = 'hrp_internal_delivery.return_move_look_two'

    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    from_location = fields.Many2One("stock.location", "from_location", select=True, readonly=True)  # 仓库存储
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    return_quantity = fields.Integer('Return Quantity', select=True, readonly=True)  # 清退数量
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)  # 药品批次
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', select=True, readonly=True)  # 有效时间
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
        ('3', u'单据错误'),
    ], 'Reason', select=True)  # 退药原因
    comment = fields.Text('Comment', select=True)  # 备注
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True, readonly=True)  # 是否直送
    examine = fields.Selection([
        ('00', u''),
        ('01', u'未审核'),
        ('02', u'已审核'),
    ], 'Examine', select=True, readonly=True)  # 退药审核


###############       二级间的内部移动     #####################
class StraightMoveLook(ModelView):
    """StraightMoveLook"""
    __name__ = 'hrp_internal_delivery.straight_move_look'

    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    code = fields.Char('code', select=True, readonly=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    proposal = fields.Float('proposal', select=True, readonly=True)  # 请领数量
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)  # 药品批次
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', select=True, readonly=True)  # 有效时间
    storage = fields.Boolean('storage', select=True)  # 确认收药


###############      二级冻结/非限制     #####################

class FrozenMoveLook(ModelView):
    """Straight Move Look"""
    __name__ = 'hrp_internal_delivery.frozen_move_look'

    shipment_id = fields.Char('Shipment_id', select=True)  # 每个单子的id
    move_id = fields.Integer('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)
    code = fields.Char('code', select=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Char('stock_level', select=True, readonly=True)  # 现有库存量
    proposal = fields.Float('proposal', select=True)  # 冻结数量
    is_collar = fields.Boolean('is_collar', select=True)  # 是否请领
    from_location = fields.Many2One('stock.location', 'from_location', select=True)
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素'),
    ], 'Starts', select=True)  # 药品类型
    retrieve_the_code = fields.Char('retrieve_the_code', select=True)  # 拼音简码
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True)
    shelf_life_expiration_date = fields.Date('shelf_life_expiration_date', select=True, readonly=True)  # 有效时间


class InternalAllocation(ModelView):
    """Internal Allocation"""
    __name__ = 'hrp_internal_delivery.internal_allocation'
    _rec_name = 'number'

    starts = fields.Selection([
        ('00', u'常规药品请领单'),
        # ('01',u'请退单'),
        # ('02',u'非限制转冻结'),
        # ('03',u'冻结转非限制'),
        ('04', u'内部调拨'),
        ('06', u'直送药品请领单'),
    ], 'Starts', select=True)  # 移动类型
    state = fields.Selection([
        ('draft', u'请领收药'),
        # ('done',u'请领完成'),
        ('00', u'内部调拨确认收货'),
        # ('01',u'内部凋拨完成'),
        ('03', u'内部调拨发药'),
        # ('04', u'请退完成'),
        # ('05', u'内部调拨发药完成'),
    ], 'State', select=True, readonly=False, sort=True)  # 状态
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
        'invisible': Equal(Eval('starts'), '01') | Equal(Eval('starts'), '02') | Equal(Eval('starts'), '03') | Equal(
            Eval('starts'), '04')
    }, depends=['starts'])
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    message_find = fields.Boolean('Find', select=True, states={
        'invisible': Equal(Eval('starts'), '00') & Equal(Eval('drug_starts'), '06') | Equal(Eval('starts'),
                                                                                            '06') & Equal(
            Eval('drug_starts'), '06')
    }, depends=['drug_starts', 'starts'])  # 查找按钮
    moves = fields.One2Many('hrp_internal_delivery.internal_move_list', '', 'Moves')

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
        if self.starts == '00' or self.starts == '06':
            self.state = 'draft'
        if self.starts == '04':
            self.state = '03'

    @staticmethod
    def default_to_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @fields.depends('starts', 'moves', 'state', 'to_location', 'message_find', 'drug_starts')
    def on_change_message_find(self):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        if self.message_find == True:
            Product = Pool().get('product.product')
            Date = Pool().get('ir.date')
            internal = Pool().get('stock.shipment.internal')

            frezz_id = {config.hospital.storage_location.id: config.hospital.freeze_location.id,  # 住院药房
                        config.outpatient_service.storage_location.id: config.outpatient_service.freeze_location.id,
                        # 门诊药房
                        config.medical.storage_location.id: config.medical.freeze_location.id,  # 体检药房
                        config.endoscopic.storage_location.id: config.endoscopic.freeze_location.id,  # 内镜药房
                        config.preparation.storage_location.id: config.preparation.freeze_location.id,  # 制剂室
                        config.ward.storage_location.id: config.ward.freeze_location.id,  # 放射科
                        config.herbs.storage_location.id: config.herbs.freeze_location.id,  # 草药房

                        }
            if self.starts == '00':  # 常规请领
                if self.drug_starts == None:
                    TestInternal = internal.search([
                        ('state', '=', self.state),
                        ('starts', '=', self.starts),
                        ('straights', '=', False),
                        ('to_location', '=', self.to_location.id),
                    ])
                else:
                    TestInternal = internal.search([
                        ('state', '=', self.state),
                        ('starts', '=', self.starts),
                        ('straights', '=', False),
                        ('to_location', '=', self.to_location.id),
                        ('drug_starts', '=', self.drug_starts),
                    ])
            elif self.starts == '04':  # 内部调拨
                if self.state == 'draft':
                    TestInternal = []
                elif self.state == 'done':
                    TestInternal = []
                elif self.state == '05':
                    TestInternal = internal.search([
                        ('state', '=', 'done'),
                        ('starts', '=', self.starts),
                        ('from_location', '=', self.to_location.id),
                    ])
                elif self.state == '00':
                    TestInternal = internal.search([
                        ('state', '=', 'draft'),
                        ('starts', '=', self.starts),
                        ('to_location', '=', self.to_location.id),
                    ])
                elif self.state == '01':
                    TestInternal = internal.search([
                        ('state', '=', 'done'),
                        ('starts', '=', self.starts),
                        ('from_location', '=', config.transfers.id),
                        ('to_location', '=', self.to_location.id),
                    ])
                elif self.state == '03':
                    TestInternal = internal.search([
                        ('state', '=', 'draft'),
                        ('starts', '=', self.starts),
                        ('to_location', '=', config.transfers.id),
                        ('from_location', '=', self.to_location.id),
                    ])
                else:
                    TestInternal = internal.search([
                        ('state', '=', self.state),
                        ('starts', '=', self.starts),
                        ('from_location', '=', self.to_location.id),
                    ])
            elif self.starts == '01':  # 判断是否为请退
                if self.state == '04':
                    TestInternal = internal.search([
                        ('state', '=', 'done'),
                        ('starts', '=', self.starts),
                        ('from_location', '=', frezz_id[self.location.id]),  # 二级药房冻结区默认配置
                    ])
                if self.state == 'done':
                    TestInternal = []
            elif self.starts == '06':  # 判断是否为直送药品请领单
                TestInternal = internal.search([
                    ('state', '=', self.state),
                    ('starts', '=', self.starts),
                    ('drug_starts', '=', self.drug_starts),
                    ('straights', '=', True),
                    ('to_location', '=', self.to_location.id),
                ])
            elif self.starts == '02':  # 判断是否为冻结/非限制
                TestInternal = internal.search([
                    ('state', '=', self.state),
                    ('starts', '=', self.starts),
                    ('from_location', '=', self.to_location.id),
                ])
            elif self.starts == '03':  # 判断是否为冻结/非限制
                TestInternal = internal.search([
                    ('state', '=', self.state),
                    ('starts', '=', self.starts),
                    ('to_location', '=', self.to_location.id),
                ])
            else:
                TestInternal = internal.search([
                    ('state', '=', self.state),
                    ('starts', '=', self.starts),
                    ('straights', '=', False),
                    ('to_location', '=', self.to_location.id),
                ])
            if TestInternal:
                test_list = []
                for i in TestInternal:
                    shipment_id = i.id
                    lv = {}
                    list = []
                    if self.state == '00':
                        lv['state'] = 'draft'
                    else:
                        lv['state'] = self.state
                    lv['move_time'] = i.planned_date
                    lv['move_number'] = str(i.number)
                    lv['shipment_id'] = shipment_id
                    if self.starts == '00':
                        lv['starts'] = '06'
                    elif self.starts == '01':
                        lv['starts'] = '05'
                    elif self.starts == '06':
                        lv['starts'] = '06'
                    elif self.starts == '02':
                        lv['starts'] = '03'
                    elif self.starts == '03':
                        lv['starts'] = '03'
                    elif self.starts == '04' and self.state != '00':
                        lv['starts'] = '00'
                    elif self.starts == '04' and self.state == '00':
                        lv['starts'] = '04'
                    else:
                        lv['starts'] = self.starts
                    lv['location'] = i.place_of_service
                    lv['from_location'] = i.from_location
                    lv['to_location'] = i.to_location
                    lv['place_of_service'] = i.place_of_service
                    lv['drug_starts'] = i.drug_starts  # 药品类型
                    Move = i.moves
                    for each in Move:
                        min_Package = each.product.min_Package.id  # 最小单位
                        uom_id = each.uom.id
                        move_id = each.id
                        dict = {}
                        dict['move_id'] = move_id  # 每条数据的id
                        name = each.product.name
                        dict['product'] = name
                        locals = each.from_location
                        if uom_id == min_Package:
                            with Transaction().set_context(stock_date_end=Date.today()):
                                quantities = Product.products_by_location([locals], [each.product.id], with_childs=True)
                            if quantities.values():
                                stock_level = [v for v in quantities.values()][0]
                            else:
                                stock_level = 0
                            factor_number = Uom.compute_qty(each.product.default_uom, stock_level,
                                                            each.product.min_Package, round=True)
                            dict['stock_level'] = str(factor_number)
                            if factor_number < each.quantity:
                                dict['prompt'] = '01'
                            else:
                                pass
                        else:
                            with Transaction().set_context(stock_date_end=Date.today()):
                                quantities = Product.products_by_location([locals], [each.product.id], with_childs=True)
                            if quantities.values():
                                stock_level = [v for v in quantities.values()][0]
                            else:
                                stock_level = 0
                            dict['stock_level'] = str(stock_level)
                            if stock_level < each.quantity:
                                dict['prompt'] = '01'
                            else:
                                pass
                        dict['code'] = str(each.product.code)
                        if each.product.a_charge == None:
                            dict['a_charge'] = ''
                        else:
                            dict['a_charge'] = str(each.product.a_charge)
                        dict['outgoing_audit'] = each.outgoing_audit
                        dict['company'] = each.uom.id
                        dict['uom'] = each.uom.id
                        dict['odd_numbers'] = each.real_number
                        dict['proposal'] = each.quantity
                        dict['is_direct_sending'] = each.is_direct_sending
                        if each.product.template.drug_specifications == None:
                            dict['drug_specifications'] = ''
                        else:
                            dict['drug_specifications'] = each.product.template.drug_specifications
                        dict['return_quantity'] = each.real_number  # 退药数量
                        dict['reason'] = each.reason  # 退药原因
                        dict['comment'] = each.comment  # 退药备注
                        dict['lot'] = each.lot  # 退药的批次
                        dict['storage'] = True  # 确认收药
                        if each.lot != None:
                            dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                        else:
                            pass
                        list.append(dict)
                    if self.starts == '06':  # 直送药品请领单
                        lv['move_look_two'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '00':  # 二级请领单
                        lv['move_look_two'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '01':  # 二级请退单
                        lv['move_return_two'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '04' and self.state != '00':  # 内部调拨单
                        lv['move_apply'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '04' and self.state == '00':  # 内部调拨单
                        lv['move_straight'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '03':  # 冻结/非限制
                        lv['move_frozen'] = sorted(list, key=operator.itemgetter('product'))
                    if self.starts == '02':  # 非限制/冻结
                        lv['move_frozen'] = sorted(list, key=operator.itemgetter('product'))
                    test_list.append(lv)
                self.moves = test_list

    @staticmethod
    def default_actives():
        return '04'

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
        return super(InternalAllocation, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        # Cancel before delete
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalAllocation, cls).delete(shipments)


class InternalAllocationWizard(Wizard):
    __name__ = 'hrp_internal_delivery.internal_allocation_wizard'

    start = StateView('hrp_internal_delivery.internal_allocation',
                      'hrp_internal_delivery.internal_allocation_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_internal_allocation')

    def do_create_(self, action):
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
                            dict['list_price'] = ProductId[0].template.list_price
                            dict['cost_price'] = ProductId[0].template.cost_price
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
                            dict['origin'] = None
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
                # whether_move = Move.assign_try(moves, grouping=('product', 'lot'))
                # internal.assign_try(Internal)
                internal.assign(Internal)
                internal.done(Internal)
            else:
                pass
        return action, {}


