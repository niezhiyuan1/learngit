# coding:utf-8
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool, Not
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['InternalApplyDirect', 'InternalApplyListDirect', 'ApplyDirectWizard', 'ApplyListExhibitionDirect']


####################     直送请领单查询     ################################

class InternalApplyDirect(ModelView):
    'Internal Apply Direct'

    __name__ = 'hrp_internal_delivery.internal_apply_direct'

    move_time = fields.Date('move_time', select=True, readonly=True)  # 时间
    move_number = fields.Char('Number', select=True, readonly=True)  # 单号
    shipment_id = fields.Char('shipment_id', select=True)  # shipment_id
    location = fields.Many2One("stock.location", "location", select=True)  # 创建的部门
    from_location = fields.Many2One("stock.location", "from_location", select=True, readonly=True)  # 来自库存地
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 到达库存地
    place_of_service = fields.Many2One("stock.location", "place_of_service", select=True, readonly=True)  # 中转库存地
    message_confirm = fields.Boolean('confirm', select=True)  # 确认
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素'),
    ], 'drug_type', select=True)  # 药品类型
    state = fields.Selection([
        ('draft',       u'起草'),
        ('assigned', u'分配'),
        ('waiting', u'等待'),
        ('done', u'完成'),
    ], 'State', select=True, readonly=False)
    moves = fields.One2Many('hrp_internal_delivery.apply_list_exhibition_direct', 'None', 'moves', domain=[
        ('drug_type', '=', Eval('drug_type'))])


##################       直送显示内容界面       #####################

class ApplyListExhibitionDirect(ModelView):
    'Apply List Exhibition Direct'
    __name__ = 'hrp_internal_delivery.apply_list_exhibition_direct'

    move_id = fields.Char('move_id', select=True)  # 每条数据的id
    product = fields.Char('product', select=True, readonly=True)  # 产品
    product_choice = fields.Many2One("product.product", "product_choice", domain=[
        ('id', 'in', Eval('product_id'))], depends=['product_id'])
    product_id = fields.Function(
        fields.One2Many('product.product', None, 'product_id', depends=['product_id', 'drug_type']),
        'on_change_with_product_id')
    code = fields.Char('code', select=True, readonly=True)  # 药品编码
    company = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    lot = fields.Many2One('stock.lot', 'lot', select=True)
    odd_numbers = fields.Float('odd_numbers', select=True, readonly=True)  # 建议请领数量
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Float('stock_level', select=True, readonly=True)  # 现有库存量
    outpatient_7days = fields.Float('Outpatient_7days', select=True, readonly=True)  # 7日量
    proposal = fields.Float('proposal', select=True)  # 请领数量
    drug_type = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u' '),
        ('07', u'同位素'),
    ], 'drug_type', select=True)  # 药品类型

    @fields.depends('drug_type', 'product_id')
    def on_change_with_product_id(self):
        UomCategory = Pool().get('product.category')
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        product = Pool().get('product.product')
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        location_id = UserId.get_user_id()
        MOVE = Pool().get('hrp_new_product.new_product')
        list_id = []
        if location_id == config.warehouse.storage_location.id:
            if self.drug_type == '01':
                uom_name = u'中成药'
            if self.drug_type == '02':
                uom_name = u'中草药'
            if self.drug_type == '04':
                uom_name = u'原料药'
            if self.drug_type == '05':
                uom_name = u'敷药'
            if self.drug_type == '00':
                uom_name = u'西药'
            if self.drug_type == '03':
                uom_name = u'颗粒中'
            if self.drug_type == '07':
                uom_name = u'同位素'
            uom_category = UomCategory.search([('name', '=', uom_name)])
            categories_id = uom_category[0].id
            Product = product.search([
                ('categories', '=', categories_id),
                ('is_direct_sending', '=', False),
            ])
            for i in Product:
                list_id.append(i.id)
        else:
            mmm = MOVE.search([
                ('drug_type', '=', self.drug_type),
                ('is_direct_sending', '=', False),
                ('to_location', '=', location_id),
            ])
            for i in mmm:
                list_id.append(i.product.id)
        return list_id

    @fields.depends('product_choice')
    def on_change_product_choice(self):
        if self.product_choice == None:
            self.product = None
            self.company = None
            self.code = None
            self.a_charge = None
            self.odd_numbers = None
            self.stock_level = None
            return
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        location_id = UserId.get_user_id()
        Date = Pool().get('ir.date')
        Product = Pool().get('product.product')
        MOVE = Pool().get('hrp_new_product.new_product')
        product = self.product_choice
        if location_id == config.warehouse.storage_location.id:
            product_change = Product.search(['id', '=', product.id])
            for i in product_change:
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([location_id], [i.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0
                self.product = i.name
                self.company = i.default_uom
                self.code = i.code
                self.a_charge = str(i.a_charge)
                self.odd_numbers = 0
                self.stock_level = float(stock_level)

        else:
            mmm = MOVE.search([
                ('product', '=', product),
                ('to_location', '=', location_id),
            ])
            for i in mmm:
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = Product.products_by_location([location_id], [i.product.id], with_childs=True)
                if quantities.values():
                    stock_level = [v for v in quantities.values()][0]
                else:
                    stock_level = 0
                self.product = i.product.name
                self.company = i.uom.id
                self.code = i.code
                self.a_charge = i.a_charge
                if i.proposal <= 0:
                    self.odd_numbers = 0
                else:
                    self.odd_numbers = i.proposal
                self.stock_level = float(stock_level)


class InternalApplyListDirect(ModelView):
    'Internal Apply List Direct'
    __name__ = 'hrp_internal_delivery.internal_apply_list_direct'
    _rec_name = 'number'

    starts = fields.Selection([
        ('06', u'直送药品请领单'),
    ], 'Starts', select=True)  # 移动类型
    state = fields.Selection([
        ('draft', u'起草'),
    ], 'State', select=True, readonly=False)  # 状态
    to_location = fields.Many2One("stock.location", "to_location", select=True, readonly=True)  # 仓库存储
    number = fields.Char('number', select=True)  # 单号
    message_find = fields.Boolean('Find', select=True)  # 查找按钮
    moves = fields.One2Many('hrp_internal_delivery.internal_apply_direct', 'None', 'Moves')

    @staticmethod
    def default_starts():
        return '06'

    @staticmethod
    def default_to_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @fields.depends('starts', 'moves', 'state', 'to_location', 'message_find', 'number')
    def on_change_message_find(self):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        if self.message_find == True:
            if self.number == '':
                if self.to_location.id == config.warehouse.storage_location.id:  # 中心药库
                    Product = Pool().get('product.product')
                    Date = Pool().get('ir.date')
                    internal = Pool().get('stock.shipment.internal')
                    MOVE = Pool().get('hrp_new_product.new_product')
                    if self.starts == '06':  # 常规请领
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('straights', '=', True),
                            ('from_location', '=', config.warehouse.storage_location.id),
                        ])
                    if TestInternal:
                        test_list = []
                        for i in TestInternal:
                            shipment_id = i.id
                            lv = {}
                            list = []
                            lv['state'] = self.state
                            lv['move_time'] = i.planned_date
                            lv['move_number'] = str(i.number)
                            lv['shipment_id'] = shipment_id
                            if self.starts == '00':
                                lv['starts'] = '06'
                            else:
                                lv['starts'] = self.starts
                            lv['location'] = i.place_of_service
                            lv['from_location'] = i.from_location
                            lv['to_location'] = i.to_location
                            lv['place_of_service'] = i.place_of_service
                            Move = i.moves
                            for each in Move:
                                move_id = each.id
                                dict = {}
                                dict['move_id'] = move_id  # 每条数据的id
                                name = each.product.name
                                dict['product'] = name
                                dict['product_choice'] = each.product.id
                                dict['code'] = str(each.product.code)
                                if each.product.a_charge == None:
                                    dict['a_charge'] = ''
                                else:
                                    dict['a_charge'] = str(each.product.a_charge)
                                dict['outgoing_audit'] = each.outgoing_audit
                                dict['company'] = each.uom.id
                                dict['uom'] = each.uom.id
                                dict['proposal'] = float(each.quantity)
                                dict['is_direct_sending'] = each.is_direct_sending
                                dict['return_quantity'] = each.real_number  # 退药数量
                                dict['reason'] = each.reason  # 退药原因
                                dict['comment'] = each.comment  # 退药备注
                                dict['lot'] = each.lot  # 退药的批次
                                with Transaction().set_context(stock_date_end=Date.today()):
                                    quantities = Product.products_by_location([config.warehouse.storage_location.id],
                                                                              [each.product.id], with_childs=True)
                                if quantities.values():
                                    stock_level = [v for v in quantities.values()][0]
                                    dict['stock_level'] = stock_level
                                else:
                                    stock_level = 0
                                modify_move = MOVE.search([
                                    ('product', '=', each.product.id),
                                ])
                                if modify_move:
                                    drug_type = modify_move[0].drug_type
                                    outpatient_7days = modify_move[0].outpatient_7days
                                    stock_levels = outpatient_7days - stock_level
                                    if stock_levels <= 0:
                                        dict['odd_numbers'] = 0.0
                                    else:
                                        dict['odd_numbers'] = float(stock_levels)
                                    lv['drug_type'] = drug_type
                                else:
                                    pass
                                if each.lot != None:
                                    dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                                else:
                                    pass
                                list.append(dict)
                            if self.starts == '06':  # 直送药品请领单
                                lv['moves'] = list
                            if self.starts == '00':  # 二级请领单
                                lv['moves'] = list
                            test_list.append(lv)
                        self.moves = test_list

                else:
                    Product = Pool().get('product.product')
                    Date = Pool().get('ir.date')
                    internal = Pool().get('stock.shipment.internal')
                    MOVE = Pool().get('hrp_new_product.new_product')
                    if self.starts == '06':  # 常规请领
                        TestInternal = internal.search([
                            ('state', '=', self.state),
                            ('starts', '=', self.starts),
                            ('straights', '=', True),
                            ('place_of_service', '=', self.to_location.id),
                        ])
                    if TestInternal:
                        test_list = []
                        for i in TestInternal:
                            shipment_id = i.id
                            lv = {}
                            list = []
                            lv['state'] = self.state
                            lv['move_time'] = i.planned_date
                            lv['move_number'] = str(i.number)
                            lv['shipment_id'] = shipment_id
                            if self.starts == '00':
                                lv['starts'] = '06'
                            else:
                                lv['starts'] = self.starts
                            lv['location'] = i.place_of_service
                            lv['from_location'] = i.from_location
                            lv['to_location'] = i.to_location
                            lv['place_of_service'] = i.place_of_service
                            Move = i.moves
                            for each in Move:
                                move_id = each.id
                                dict = {}
                                dict['move_id'] = move_id  # 每条数据的id
                                name = each.product.name
                                dict['product'] = name
                                dict['product_choice'] = each.product.id
                                dict['code'] = str(each.product.code)
                                if each.product.a_charge == None:
                                    dict['a_charge'] = ''
                                else:
                                    dict['a_charge'] = str(each.product.a_charge)
                                dict['outgoing_audit'] = each.outgoing_audit
                                dict['company'] = each.uom.id
                                dict['uom'] = each.uom.id
                                dict['proposal'] = float(each.quantity)
                                dict['is_direct_sending'] = each.is_direct_sending
                                dict['return_quantity'] = each.real_number  # 退药数量
                                dict['reason'] = each.reason  # 退药原因
                                dict['comment'] = each.comment  # 退药备注
                                dict['lot'] = each.lot  # 退药的批次
                                with Transaction().set_context(stock_date_end=Date.today()):
                                    quantities = Product.products_by_location([self.to_location.id], [each.product.id],
                                                                              with_childs=True)
                                if quantities.values():
                                    stock_level = [v for v in quantities.values()][0]
                                    dict['stock_level'] = stock_level
                                else:
                                    stock_level = 0
                                modify_move = MOVE.search([
                                    ('product', '=', each.product.id),
                                    ('to_location', '=', self.to_location.id),
                                ])
                                if modify_move:
                                    drug_type = modify_move[0].drug_type
                                    outpatient_7days = modify_move[0].outpatient_7days
                                    stock_levels = outpatient_7days - stock_level
                                    if stock_levels <= 0:
                                        dict['odd_numbers'] = 0.0
                                    else:
                                        dict['odd_numbers'] = float(stock_levels)
                                    lv['drug_type'] = drug_type
                                else:
                                    pass
                                if each.lot != None:
                                    dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                                else:
                                    pass
                                list.append(dict)
                            if self.starts == '06':  # 直送药品请领单
                                lv['moves'] = list
                            if self.starts == '00':  # 二级请领单
                                lv['moves'] = list
                            test_list.append(lv)
                        self.moves = test_list


            else:
                if self.to_location.id == config.warehouse.storage_location.id:
                    Product = Pool().get('product.product')
                    Date = Pool().get('ir.date')
                    internal = Pool().get('stock.shipment.internal')
                    MOVE = Pool().get('hrp_new_product.new_product')
                    if self.starts == '00':  # 常规请领
                        TestInternal = internal.search([
                            ('number', '=', self.number)
                        ])
                    if TestInternal:
                        test_list = []
                        for i in TestInternal:
                            shipment_id = i.id
                            lv = {}
                            list = []
                            lv['state'] = self.state
                            lv['move_time'] = i.planned_date
                            lv['move_number'] = str(i.number)
                            lv['shipment_id'] = shipment_id
                            if self.starts == '00':
                                lv['starts'] = '06'
                            else:
                                lv['starts'] = self.starts
                            lv['location'] = i.place_of_service
                            lv['from_location'] = i.from_location
                            lv['to_location'] = i.to_location
                            lv['place_of_service'] = i.place_of_service
                            Move = i.moves
                            for each in Move:
                                move_id = each.id
                                dict = {}
                                dict['move_id'] = move_id  # 每条数据的id
                                name = each.product.name
                                dict['product'] = name
                                dict['product_choice'] = each.product.id
                                dict['code'] = str(each.product.code)
                                if each.product.a_charge == None:
                                    dict['a_charge'] = ''
                                else:
                                    dict['a_charge'] = str(each.product.a_charge)
                                dict['outgoing_audit'] = each.outgoing_audit
                                dict['company'] = each.uom.id
                                dict['uom'] = each.uom.id
                                dict['proposal'] = float(each.quantity)
                                dict['is_direct_sending'] = each.is_direct_sending
                                dict['return_quantity'] = each.real_number  # 退药数量
                                dict['reason'] = each.reason  # 退药原因
                                dict['comment'] = each.comment  # 退药备注
                                dict['lot'] = each.lot  # 退药的批次
                                with Transaction().set_context(stock_date_end=Date.today()):
                                    quantities = Product.products_by_location([config.warehouse.storage_location.id],
                                                                              [each.product.id], with_childs=True)
                                if quantities.values():
                                    stock_level = [v for v in quantities.values()][0]
                                    dict['stock_level'] = stock_level
                                else:
                                    stock_level = 0
                                modify_move = MOVE.search([
                                    ('product', '=', each.product.id),
                                ])
                                drug_type = modify_move[0].drug_type
                                outpatient_7days = modify_move[0].outpatient_7days
                                stock_levels = outpatient_7days - stock_level
                                if stock_levels <= 0:
                                    dict['odd_numbers'] = 0.0
                                else:
                                    dict['odd_numbers'] = float(stock_levels)
                                lv['drug_type'] = drug_type
                                if each.lot != None:
                                    dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                                else:
                                    pass
                                list.append(dict)
                            if self.starts == '06':  # 直送药品请领单
                                lv['moves'] = list
                            if self.starts == '00':  # 二级请领单
                                lv['moves'] = list
                            test_list.append(lv)
                        self.moves = test_list
                    else:
                        pass

                else:
                    Product = Pool().get('product.product')
                    Date = Pool().get('ir.date')
                    internal = Pool().get('stock.shipment.internal')
                    MOVE = Pool().get('hrp_new_product.new_product')
                    if self.starts == '06':  # 常规请领
                        TestInternal = internal.search([
                            ('number', '=', self.number)
                        ])
                    if TestInternal:
                        test_list = []
                        for i in TestInternal:
                            shipment_id = i.id
                            lv = {}
                            list = []
                            lv['state'] = self.state
                            lv['move_time'] = i.planned_date
                            lv['move_number'] = str(i.number)
                            lv['shipment_id'] = shipment_id
                            if self.starts == '00':
                                lv['starts'] = '06'
                            else:
                                lv['starts'] = self.starts
                            lv['location'] = i.place_of_service
                            lv['from_location'] = i.from_location
                            lv['to_location'] = i.to_location
                            lv['place_of_service'] = i.place_of_service
                            Move = i.moves
                            for each in Move:
                                move_id = each.id
                                dict = {}
                                dict['move_id'] = move_id  # 每条数据的id
                                name = each.product.name
                                dict['product'] = name
                                dict['product_choice'] = each.product.id
                                dict['code'] = str(each.product.code)
                                if each.product.a_charge == None:
                                    dict['a_charge'] = ''
                                else:
                                    dict['a_charge'] = str(each.product.a_charge)
                                dict['outgoing_audit'] = each.outgoing_audit
                                dict['company'] = each.uom.id
                                dict['uom'] = each.uom.id
                                dict['proposal'] = float(each.quantity)
                                dict['is_direct_sending'] = each.is_direct_sending
                                dict['return_quantity'] = each.real_number  # 退药数量
                                dict['reason'] = each.reason  # 退药原因
                                dict['comment'] = each.comment  # 退药备注
                                dict['lot'] = each.lot  # 退药的批次
                                with Transaction().set_context(stock_date_end=Date.today()):
                                    quantities = Product.products_by_location([self.to_location.id],
                                                                              [each.product.id], with_childs=True)
                                if quantities.values():
                                    stock_level = [v for v in quantities.values()][0]
                                    dict['stock_level'] = stock_level
                                else:
                                    stock_level = 0
                                mmm = MOVE.search([
                                    ('product', '=', each.product.id),
                                ])
                                drug_type = mmm[0].drug_type
                                outpatient_7days = mmm[0].outpatient_7days
                                stock_levels = outpatient_7days - stock_level
                                if stock_levels <= 0:
                                    dict['odd_numbers'] = 0.0
                                else:
                                    dict['odd_numbers'] = float(stock_levels)
                                lv['drug_type'] = drug_type
                                if each.lot != None:
                                    dict['shelf_life_expiration_date'] = each.lot.shelf_life_expiration_date
                                else:
                                    pass
                                list.append(dict)
                            if self.starts == '06':  # 直送药品请领单
                                lv['moves'] = list
                            if self.starts == '00':  # 二级请领单
                                lv['moves'] = list
                            test_list.append(lv)
                        self.moves = test_list

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class ApplyDirectWizard(Wizard):
    'Apply Direct Wizard'

    __name__ = 'hrp_internal_delivery.apply_direct_wizard'

    start = StateView('hrp_internal_delivery.internal_apply_list_direct',
                      'hrp_internal_delivery.internal_apply_list_direct_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_internal_apply_list')

    def do_create_(self, action):
        pass
