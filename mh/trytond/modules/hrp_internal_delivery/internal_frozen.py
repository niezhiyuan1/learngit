# coding:utf-8
import decimal
from trytond.model import ModelView, fields
from trytond.modules.product import Uom
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['InternalFrozen', 'InternalFrozenWizard', 'TestFrozen']

STATES = {
    'readonly': ~Eval('is_collar', True),
}


class TestFrozen(ModelView):
    """Test Frozen"""
    __name__ = 'hrp_internal_delivery.test_frozen'
    _rec_name = 'number'

    product = fields.Many2One("product.product", "Product", required=True,
                              domain=[
                                  ('id', 'in', Eval('product_condition'))],
                              depends=['from_location', 'product_condition'])  # 产品
    product_condition = fields.Function(
        fields.One2Many('product.product', 'None', 'product_condition', depends=['product', 'from_location']),
        'on_change_with_product_condition')

    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品
    code = fields.Char('code', select=True)  # 编码
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', domain=[
        ('category', '=', Eval('product_uom_category')),
    ], required=False, select=False, depends=['product_uom_category', ])  # 单位
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    stock_level = fields.Char('stock_level', select=True, readonly=True)  # 现有库存量
    proposal = fields.Float('proposal', select=True, states=STATES
                            , depends=['is_collar'])  # 请领数量
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
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
        ('product', '=', Eval('product')),
        ('id', 'in', Eval('lots')),
    ], context={
        'locations': [Eval('from_location')],
    }, readonly=False, depends=['product', 'from_location', 'lots'], required=True)
    lots = fields.Function(fields.One2Many('stock.lot', '', 'Lot', depends=['product', 'from_location', 'lots']),
                           'on_change_with_lots')

    @fields.depends('product', 'from_location')
    def on_change_with_lots(self):
        if self.from_location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.from_location], with_childs=True, grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value != 0:
                        if key[-1] != None:
                            hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('product', 'from_location')
    def on_change_with_product_condition(self):
        if self.from_location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.from_location.id], with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value != 0:
                        hrp_quantity.append(key[1])
                return hrp_quantity

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('product', 'from_location')
    def on_change_product(self):
        if self.product:
            UomCategory = Pool().get('product.category')
            ProductMove = Pool().get('product.product')
            product = self.product.id
            product_move = ProductMove.search([
                ('id', '=', product)
            ])
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            if self.from_location:
                with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                    pbl = Product.products_by_location([self.from_location], with_childs=True,
                                                       grouping=('product', 'lot'))
                    hrp_quantity = []
                    for key, value in pbl.items():
                        if value != 0:
                            hrp_quantity.append(key[2])
                    self.lots = hrp_quantity
            for i in product_move:
                self.product_name = i.template.name
                self.code = str(i.code)
                self.drug_specifications = str(i.template.drug_specifications)
                self.uom = i.template.default_uom.id
                if i.template.a_charge == None:
                    self.a_charge = ''
                else:
                    self.a_charge = str(i.template.a_charge)
                self.retrieve_the_code = i.retrieve_the_code
                categories_id = self.product.template.categories[0].id
                uom_category = UomCategory.search([('id', '=', categories_id)])
                uom_name = uom_category[0].name
                if uom_name == u'中成药':
                    self.drug_type = '01'
                if uom_name == u'中草药':
                    self.drug_type = '02'
                if uom_name == u'原料药':
                    self.drug_type = '04'
                if uom_name == u'敷药':
                    self.drug_type = '05'
                if uom_name == u'西药':
                    self.drug_type = '00'
                if uom_name == u'颗粒中':
                    self.drug_type = '03'
                if uom_name == u'同位素':
                    self.drug_type = '07'
                if uom_name == '':
                    self.drug_type = '06'
        else:
            self.product_name = None
            self.code = None
            self.drug_specifications = None
            self.uom = None
            self.retrieve_the_code = None
            self.a_charge = None
            self.drug_type = None

    @fields.depends('proposal', 'lot', 'from_location', 'product', 'uom')
    def on_change_proposal(self):
        Date = Pool().get('ir.date')
        Product = Pool().get('product.product')
        location = self.from_location.id
        product_id = self.product.id
        product = self.product
        min_Package = product.min_Package.id
        uom_id = self.uom.id
        if str(self.proposal).split('.')[1] != '0':
            return self.raise_user_error(u'请输入整数')
        if self.lot:
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location([location], with_childs=True, grouping=('product', 'lot'))
                hrp_quantity = {}
                for key, value in pbl.items():
                    if value != 0:
                        hrp_quantity[(key[2])] = value
                lots_number = hrp_quantity[self.lot.id]
                if uom_id == min_Package:
                    factor_number = Uom.compute_qty(product.default_uom, lots_number, product.min_Package, round=True)
                    if self.proposal > factor_number:
                        return self.raise_user_error(u'超过库存数量')
                    else:
                        pass
                else:
                    lot_number = hrp_quantity[self.lot.id]
                    if self.proposal > lot_number:
                        return self.raise_user_error(u'超过库存数量')
                    else:
                        pass
        else:
            with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):
                pbl = Product.products_by_location([location], [product_id], with_childs=True)
                sum_value = 0
                for key, value in pbl.items():
                    if value != 0:
                        sum_value += value
                if uom_id == min_Package:
                    factor_number = Uom.compute_qty(product.default_uom, sum_value, product.min_Package, round=True)
                    if self.proposal > factor_number:
                        return self.raise_user_error(u'超过库存数量')
                    else:
                        pass
                else:
                    if self.proposal > sum_value:
                        return self.raise_user_error(u'超过库存数量')
                    else:
                        pass

    @staticmethod
    def default_is_collar():
        return True

    @staticmethod
    def default_drug_type():
        return '06'


class InternalFrozen(ModelView):
    """Internal Frozen"""

    __name__ = 'hrp_internal_delivery.internal_frozen'
    _rec_name = 'number'

    number = fields.Char('Number', size=None, select=True, readonly=False)
    effective_date = fields.Date('Effective Date',
                                 states={
                                     'readonly': Eval('state').in_(['cancel', 'done']),
                                 },
                                 depends=['state'])
    planned_date = fields.Date('Planned Date', readonly=True)
    type = fields.Selection(
        [('02', u'非限制转冻结'),
         ('03', u'冻结转非限制'),
         ],
        'Type', select=True, required=True, states={
            'readonly': Bool(Eval('moves')),
        })
    from_location = fields.Many2One('stock.location', 'from_location', readonly=True, domain=[
        ('from_location', '=', Eval('from_location')),
    ])
    to_location = fields.Many2One('stock.location', 'to_location', readonly=True)
    moves = fields.One2Many('hrp_internal_delivery.test_frozen', '', 'Moves',
                            states={
                                'readonly': ~Eval('from_location') | ~Eval('to_location'),
                            }
                            ,
                            domain=[
                                ('from_location', '=', Eval('from_location')),
                            ])

    @fields.depends('type', 'from_location', 'to_location')
    def on_change_type(self):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        Group = Pool().get("res.group")
        ZY = Group.search(['name', '=', 'MH-住院药房'])
        MZ = Group.search(['name', '=', 'MH-门诊药房'])
        ZX = Group.search(['name', '=', 'MH-中心药库'])
        TJ = Group.search(['name', '=', 'MH-体检药房'])
        NJ = Group.search(['name', '=', 'MH-内镜药房'])
        ZJ = Group.search(['name', '=', 'MH-制剂室'])
        FS = Group.search(['name', '=', 'MH-放射科'])
        CY = Group.search(['name', '=', 'MH-草药房'])
        zy_list_id = []
        mz_list_id = []
        zx_list_id = []
        tj_list_id = []
        nj_list_id = []
        zj_list_id = []
        fs_list_id = []
        cy_list_id = []
        if ZY:
            zy_user = ZY[0].users
            for i in zy_user:
                zy_list_id.append(i.id)
        if MZ:
            mz_user = MZ[0].users
            for i in mz_user:
                mz_list_id.append(i.id)
        if ZX:
            zx_user = ZX[0].users
            for i in zx_user:
                zx_list_id.append(i.id)
        if TJ:
            tj_user = TJ[0].users
            for i in tj_user:
                tj_list_id.append(i.id)
        if NJ:
            nj_user = NJ[0].users
            for i in nj_user:
                nj_list_id.append(i.id)
        if ZJ:
            zj_user = ZJ[0].users
            for i in zj_user:
                zj_list_id.append(i.id)
        if FS:
            fs_user = FS[0].users
            for i in fs_user:
                fs_list_id.append(i.id)
        if CY:
            cy_user = CY[0].users
            for i in cy_user:
                cy_list_id.append(i.id)
        user_from_location = 0
        user_to_location = 0
        user_id = Transaction().user
        if user_id == 1:
            user_from_location = config.warehouse.storage_location.id  # 中心药房
            user_to_location = config.return_of.id  # 药房动冻结区
        if user_id in zy_list_id:
            user_from_location = config.hospital.storage_location.id  # 住院药房
            user_to_location = config.hospital_freeze.id  # 住院冻结区hospital_freeze
        if user_id in mz_list_id:
            user_from_location = config.outpatient_service.storage_location.id  # 门诊药房
            user_to_location = config.outpatient_freeze.id  # 门诊冻结区outpatient_freeze
        if user_id in zx_list_id:
            user_from_location = config.warehouse.storage_location.id  # 中心药库
            user_to_location = config.return_of.id  # 药房冻结区
        if user_id in tj_list_id:
            user_from_location = config.medical.storage_location.id  # 体检药房
            user_to_location = config.medical.freeze_location.id  # 体检药房冻结区
        if user_id in nj_list_id:
            user_from_location = config.endoscopic.storage_location.id  # 内镜药房
            user_to_location = config.endoscopic.freeze_location.id  # 内镜药房冻结区
        if user_id in zj_list_id:
            user_from_location = config.preparation.storage_location.id  # 制剂室
            user_to_location = config.preparation.freeze_location.id  # 制剂室冻结区
        if user_id in fs_list_id:
            user_from_location = config.ward.storage_location.id  # 放射科
            user_to_location = config.ward.freeze_location.id  # 放射科冻结区
        if user_id in cy_list_id:
            user_from_location = config.herbs.storage_location.id  # 草药房
            user_to_location = config.herbs.freeze_location.id  # 草药房冻结区
        if self.type == '02':
            self.from_location = user_from_location
            self.to_location = user_to_location
        else:
            self.from_location = user_to_location
            self.to_location = user_from_location

    @staticmethod
    def default_planned_date():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

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
        return super(InternalFrozen, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        # Cancel before delete
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalFrozen, cls).delete(shipments)


class InternalFrozenWizard(Wizard):
    __name__ = 'hrp_internal_delivery.internal_frozen_wizard'

    start = StateView('hrp_internal_delivery.internal_frozen',
                      'hrp_internal_delivery.internal_frozen_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_internal_frozen')

    def do_create_(self, action):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        ShipmentInternal = Pool().get('stock.shipment.internal')
        internal = Pool().get('stock.shipment.internal')
        MoveNumber = Pool().get('stock.move')
        new_return = Pool().get('hrp_new_product.new_return')
        Product = Pool().get('product.product')
        UOM = Pool().get('product.uom')
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        lv = {}
        lv['company'] = 1
        lv['starts'] = data['start']['type']
        lv['to_location'] = data['start']['to_location']
        lv['from_location'] = data['start']['from_location']
        lv['state'] = u'draft'
        if data['start']['type'] == '02':
            states = '02'
        else:
            states = '03'
        Move = data['start']['moves']
        list = []
        for each in Move:
            if each['is_collar'] == True:
                dict = {}
                dict['origin'] = None  # each['origin']
                dict['to_location'] = data['start']['to_location']
                dict['product'] = each['product']
                dict['from_location'] = data['start']['from_location']
                dict['invoice_lines'] = ()  # each['invoice_lines']
                dict['company'] = 1  # each['company']
                dict['unit_price'] = None  # each['unit_price']产品的价格
                dict['lot'] = each['lot']  # 产品批次
                dict['uom'] = each['uom']  # 产品单位
                dict['starts'] = states
                dict['real_number'] = each['proposal']  # 产品的请领数量
                dict['quantity'] = each['proposal']

                ProductUom = Product.search([('id', '=', each['product'])])
                uom = ProductUom[0].template.default_uom
                cost_p = Product.search([('id', '=', each['product'])])[0].cost_price
                list_p = Product.search([('id', '=', each['product'])])[0].list_price
                eachuom = UOM.search([('id', '=', each['uom'])])[0]

                cost_prices = Uom.compute_price(uom, cost_p, eachuom)
                list_prices = Uom.compute_price(uom, list_p, eachuom)

                done_list = decimal.Decimal(
                    str(float(list_prices * decimal.Decimal(str(each['proposal'])))))  # 批发总价
                list_price = decimal.Decimal(done_list).quantize(decimal.Decimal('0.00'))

                done_cost = decimal.Decimal(
                    str(float(cost_prices * decimal.Decimal(str(each['proposal'])))))  # 零售总价
                cost_price = decimal.Decimal(done_cost).quantize(decimal.Decimal('0.00'))

                dict['list_price'] = list_price
                dict['cost_price'] = cost_price

                list.append(dict)
                lv['moves'] = [['create', list]]
                lv['planned_date'] = data['start']['planned_date']
                hrp_new_return = new_return.search([
                    ('product', '=', each['product']),
                    ('to_location', '=', data['start']['to_location']),
                    ('from_location', '=', data['start']['from_location']),
                ])
                if hrp_new_return:
                    return_dicts = {}
                    number = hrp_new_return[0].return_quantity
                    if number == None:
                        number = 0
                    Numbe = number + each['proposal']
                    return_dicts['return_quantity'] = Numbe
                    new_return.write(hrp_new_return, return_dicts)
                else:
                    if data['start']['type'] == '03':
                        pass
                    else:
                        return_dict = {}
                        return_dict['return_quantity'] = each['proposal']  # 产品的冻结/非限制数量
                        return_dict['to_location'] = data['start']['to_location']
                        return_dict['code'] = each['code']
                        return_dict['product'] = each['product']
                        return_dict['drug_specifications'] = each['drug_specifications']
                        return_dict['from_location'] = data['start']['from_location']
                        if data['start']['from_location'] == config.warehouse.storage_location.id:
                            return_dict['examine'] = '00'
                        else:
                            return_dict['examine'] = '01'
                        return_dict['drug_type'] = each['drug_type']
                        return_dict['retrieve_the_code'] = each['retrieve_the_code']
                        return_dict['lot'] = each['lot']  # 产品批次
                        # return_dict['list_price'] = done_list
                        # return_dict['cost_price'] = done_cost
                        ProductUom = Product.search([('id', '=', each['product'])])
                        uom = ProductUom[0].template.default_uom.id
                        return_dict['uom'] = uom
                        new_return.create([return_dict])  # 创建到退药的表

        internal.create([lv])
        Internal = internal.search([
            ('to_location', '=', data['start']['to_location']),
            ('from_location', '=', data['start']['from_location']),
            ('planned_date', '=', data['start']['planned_date']),
            ('starts', '=', data['start']['type']),
        ])
        moves1 = Internal[0].moves
        move_id = []
        for i in moves1:
            move_id.append(i.id)
        move_ = MoveNumber.search([('id', 'in', move_id)])
        move_number = MoveNumber.assign_try(move_, grouping=('product', 'lot'))
        ShipmentInternal.wait(Internal)
        ShipmentInternal.assign(Internal)
        ShipmentInternal.done(Internal)
        if move_number == True:
            ShipmentInternal.wait(Internal)
            ShipmentInternal.assign(Internal)
            ShipmentInternal.done(Internal)
        else:
            product_name = move_[0].product.name
            product_lot = move_[0].lot.number
            return self.raise_user_error(product_name + u',批次:' + product_lot + u'实际数量有变 请删除该行项目后 重新输入')
        return action, {}
