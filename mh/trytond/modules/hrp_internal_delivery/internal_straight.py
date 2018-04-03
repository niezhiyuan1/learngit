# coding:utf-8
import decimal
import operator
from time import strftime, localtime
import calendar
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If, Equal, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction
import time

__all__ = ['InternalStraights', 'InternalStraightsWizard', 'TestStraight']

year = strftime("%Y", localtime())
mon = strftime("%m", localtime())
day = strftime("%d", localtime())

class TestStraight(ModelView):
    'Test Straight'

    __name__ = 'hrp_internal_delivery.test_straight'
    _rec_name = 'number'

    product = fields.Many2One("product.product", "Product", required=True, depends=['products'],
                              domain=[('id', 'in', Eval('products'))])  # 产品
    products = fields.Function(fields.One2Many("product.product", "", "Product"), 'on_change_with_products')  # 二级库中的药品
    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品名字
    code = fields.Char('code', select=True, readonly=True)  # 编码
    from_location = fields.Many2One('stock.location', 'from_location', select=True)
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    uom = fields.Many2One('product.uom', 'company', select=True, readonly=True)  # 单位
    a_charge = fields.Char('a_charge', select=True, readonly=True)  # 件装量
    proposal = fields.Float('proposal', select=True, depends=['is_direct_sending', 'is_collar'], states={
        'readonly': ~Eval('is_collar', True),
    })
    stock_level = fields.Char('stock_level', select=True)  # 当前库存数
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
        ('product', '=', Eval('product')),
        ('id', 'in', Eval('lots')),
    ], context={
        'locations': [Eval('from_location')],
    }, readonly=False, depends=['product', 'from_location', 'lots'])
    lots = fields.Function(fields.One2Many('stock.lot', '', 'Lot', depends=['product', 'from_location', 'lots']),
                           'on_change_with_lots')
    is_collar = fields.Boolean('is_collar', select=True)  # 是否请领

    @fields.depends('product', 'from_location')
    def on_change_with_lots(self):
        if self.from_location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            Lot = Pool().get('stock.lot')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.from_location], with_childs=True, grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value != 0:
                        if key[-1] != None:
                            hrp_quantity.append(key[2])
                return hrp_quantity

    @classmethod
    def get_user_frozen_id(cls):
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
        user_id = Transaction().user
        if user_id == 1:
            return config.return_of.id  # 中心药库冻结区
        if user_id in zy_list_id:
            return config.hospital_freeze.id  # 住院冻结区
        if user_id in mz_list_id:
            return config.outpatient_freeze.id  # 门诊冻结区
        if user_id in zx_list_id:
            return config.return_of.id  # 中心药库冻结区
        if user_id in tj_list_id:
            return config.medical.freeze_location.id  # 体检药房冻结区
        if user_id in nj_list_id:
            return config.endoscopic.freeze_location.id  # 内镜药房冻结区
        if user_id in zj_list_id:
            return config.preparation.freeze_location.id  # 制剂室冻结区
        if user_id in fs_list_id:
            return config.ward.freeze_location.id  # 放射科冻结区
        if user_id in cy_list_id:
            return config.herbs.freeze_location.id  # 草药房冻结区

    @classmethod
    def get_warehouse_frozen_id(cls):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        return [
            {'warehouse': config.warehouse.id, 'freeze': config.return_of.id},
            {'warehouse': config.hospital.id, 'freeze': config.hospital_freeze.id},
            {'warehouse': config.outpatient_service.id, 'freeze': config.outpatient_freeze.id},
            {'warehouse': config.medical.id, 'freeze': config.medical.freeze_location.id},
            {'warehouse': config.endoscopic.id, 'freeze': config.endoscopic.freeze_location.id},
            {'warehouse': config.preparation.id, 'freeze': config.preparation.freeze_location.id},
            {'warehouse': config.ward.id, 'freeze': config.ward.freeze_location.id},
            {'warehouse': config.herbs.id, 'freeze': config.herbs.freeze_location.id},
        ]

    @classmethod
    def get_user_id(cls):
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
        user_id = Transaction().user
        if user_id == 1:
            return config.warehouse.storage_location.id  # 中心药库
        if user_id in zy_list_id:
            return config.hospital.storage_location.id  # 住院
        if user_id in mz_list_id:
            return config.outpatient_service.storage_location.id  # 门诊
        if user_id in zx_list_id:
            return config.warehouse.storage_location.id  # 中心药库
        if user_id in tj_list_id:
            return config.medical.storage_location.id  # 体检药房
        if user_id in nj_list_id:
            return config.endoscopic.storage_location.id  # 内镜药房
        if user_id in zj_list_id:
            return config.preparation.storage_location.id  # 制剂室
        if user_id in fs_list_id:
            return config.ward.storage_location.id  # 放射科
        if user_id in cy_list_id:
            return config.herbs.storage_location.id  # 草药房

    @classmethod
    def get_user_warehouse(cls):
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
        user_id = Transaction().user
        if user_id == 1:
            return config.warehouse.id  # 中心药库
        if user_id in zy_list_id:
            return config.hospital.id  # 住院
        if user_id in mz_list_id:
            return config.outpatient_service.id  # 门诊
        if user_id in zx_list_id:
            return config.warehouse.id  # 中心药库
        if user_id in tj_list_id:
            return config.medical.id  # 体检药房
        if user_id in nj_list_id:
            return config.endoscopic.id  # 内镜药房
        if user_id in zj_list_id:
            return config.preparation.id  # 制剂室
        if user_id in fs_list_id:
            return config.ward.id  # 放射科
        if user_id in cy_list_id:
            return config.herbs.id  # 草药房

    @classmethod
    def get_all_warehouse(cls):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        return [config.hospital.id, config.outpatient_service.id, config.warehouse.id, config.medical.id,
                config.endoscopic.id, config.preparation.id, config.ward.id, config.herbs.id]

    @classmethod
    def get_apply_number(cls, from_id):
        internal = Pool().get('stock.shipment.internal')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
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
        if from_id in Keys:
            start_number = sequence_dict[from_id]
            start_ = start_number + '20'
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
                    return NumberSequence
                else:
                    number_int = int(number_sequence) + 1
                    EndNumber = str(number_int).zfill(4)
                    NumberSequence = start_number + str(date) + str(EndNumber)
                    return NumberSequence
            else:
                NumberSequence = start_number + date + '0001'
                return NumberSequence
        else:
            NumberSequence = start_number + date + '0001'
            return NumberSequence

    @staticmethod
    def get_default_moves_now():
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
        ])
        for each in mmm:
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
                        dict_one['product'] = each.product.id
                        dict_one['return_quantity'] = quantity
                        list.append(dict_one)

                    else:
                        if lo == 0:
                            lot_quant_one = warehouse_quant[
                                (each.to_location.id, each.product.id, done_list[lo])]
                            dict_two = {}
                            dict_two['product'] = each.product.id
                            dict_two['return_quantity'] = lot_quant_one
                            list.append(dict)
                        elif lo == num - 1:
                            lot_quant_two = warehouse_quant[
                                (each.to_location.id, each.product.id, done_list[lo])]
                            Quantity = lot_quant_two - (number - quantity)
                            dict['product'] = each.product.id
                            dict['return_quantity'] = Quantity
                            list.append(dict_two)
                        else:
                            lot_quant_three = warehouse_quant[
                                (each.to_location.id, each.product.id, done_list[lo])]
                            dict_three = {}
                            dict_three['product'] = each.product.id
                            dict_three['return_quantity'] = lot_quant_three
                            list.append(dict_three)
        return list

    @fields.depends('from_location')
    def on_change_with_products(self):
        if self.from_location:
            UserId = Pool().get('hrp_internal_delivery.test_straight')
            location_id = UserId.get_user_id()
            OrderPoint = Pool().get('stock.order_point')
            orderpoints = OrderPoint.search([
                ('type', '=', 'internal'),
                ('storage_location', '=', location_id),
            ])
            hrp_product_id = []
            for i in orderpoints:
                hrp_product_id.append(i.product.id)
            return hrp_product_id

    @fields.depends('product', 'from_location')
    def on_change_product(self):
        if self.product:
            UserId = Pool().get('hrp_internal_delivery.test_straight')
            location_id = UserId.get_user_id()
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            MOVE = Pool().get('hrp_new_product.new_product')
            product = self.product
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
                self.stock_level = stock_level
                self.product_name = i.product.name
                self.code = str(i.code)
                self.drug_specifications = i.drug_specifications
                self.uom = i.uom.id
                self.a_charge = i.a_charge
                self.stock_level = str(i.stock_level)
                self.outpatient_7days = i.outpatient_7days
                self.is_direct_sending = i.is_direct_sending
                self.lot = i.lot
        else:
            pass


class InternalStraights(ModelView):
    'Internal Straights'
    __name__ = 'hrp_internal_delivery.internal_straights'
    _rec_name = 'number'

    product = fields.Many2One('product.product', 'prodtct', select=True)  # 药品编码
    proposal = fields.Float('proposal', select=True)  # 请领数量
    uom = fields.Many2One('product.uom', 'uom', domain=[
        ('category', '=', Eval('product_uom_category')),
    ], required=False, select=False, depends=['product_uom_category', ])  # 单位
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    number = fields.Char('Number', size=None, select=True, readonly=False)
    planned_date = fields.Date('Planned Date', readonly=True)
    moves = fields.One2Many('hrp_internal_delivery.test_straight', '', 'Moves',
                            states={
                                'readonly': ~Eval('from_location') | ~Eval('to_location'),
                            }
                            ,
                            domain=[
                                ('from_location', '=', Eval('from_location')),
                            ])

    type = fields.Selection(
        [('04', u'内部调拨'),
         ],
        'Type', select=True, required=True)

    from_location = fields.Many2One('stock.location', 'from_location', depends=['from_location_two'],
                                    domain=[('id', 'in', Eval('from_location_two'))], required=True, states={
            'readonly': Bool(Eval('moves'))})
    from_location_two = fields.Function(fields.One2Many('stock.location', '', 'from_location_two'),
                                        'on_change_with_from_location_two')  # 内部调拨到达库存地
    to_location = fields.Many2One('stock.location', 'to_location', select=True)  # 到达库存地
    message_confirm = fields.Boolean('message_confirm', select=True)  # 确认按钮

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('product', 'from_location', 'to_location')
    def on_change_from_location(self):
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        Product = Pool().get('product.product')
        if self.from_location.id == config.preparation.storage_location.id:  # 临时采购
            list = []
            mmm = Product.search([('homemade', '=', True)])
            for i in mmm:
                dict = {}
                dict['code'] = i.code
                dict['product'] = i.id
                dict['product_name'] = i.name
                dict['drug_specifications'] = i.drug_specifications  # 件装量
                dict['uom'] = i.template.default_uom  # 单位uom
                dict['a_charge'] = i.a_charge
                list.append(dict)
            self.moves = list

    @fields.depends('product', 'to_location', 'proposal', 'from_location', 'message_confirm', 'uom')
    def on_change_message_confirm(self):
        if self.message_confirm == True:
            Product = Pool().get('product.product')
            list = []
            if str(self.proposal).split('.')[1] != '0':
                return self.raise_user_error(u'请输入整数')
            if self.proposal == None:
                self.raise_user_error(u"数量为必填项")
            if self.from_location == None:
                self.raise_user_error(u"来自部门为必填项")
            product_move = Product.search([
                ('id', '=', self.product.id),
            ])
            if product_move:
                dict = {}
                dict['code'] = product_move[0].code
                dict['product'] = self.product.id
                dict['product_name'] = product_move[0].name
                dict['drug_specifications'] = product_move[0].drug_specifications  # 件装量
                dict['uom'] = self.uom  # 单位uom
                dict['a_charge'] = product_move[0].a_charge
                dict['proposal'] = self.proposal
                dict['is_collar'] = True
                list.append(dict)
            self.moves = list
            self.product = None
            self.uom = None
            self.message_confirm = False
            self.proposal = None
            self.is_collar = True

    @fields.depends('product')
    def on_change_product(self):
        if self.product == None:
            self.uom = None
            pass
        else:
            Product = Pool().get('product.product')
            product = self.product.id
            mmm = Product.search([
                ('id', '=', product),
            ])
            for i in mmm:
                self.uom = i.template.default_uom.id

    @fields.depends('to_location')
    def on_change_with_from_location_two(self):
        if self.to_location:
            Config = Pool().get('purchase.configuration')
            config = Config(1)
            ZY_id = config.hospital.storage_location.id  # 住院药房
            MZ_id = config.outpatient_service.storage_location.id  # 门诊药房
            TJ_id = config.medical.storage_location.id  # 体检药房
            NJ_id = config.endoscopic.storage_location.id  # 内镜药房
            ZJ_id = config.preparation.storage_location.id  # 制剂室
            FS_id = config.ward.storage_location.id  # 放射科
            CY_id = config.herbs.storage_location.id  # 草药房
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
            user_id = Transaction().user
            if user_id == 1:
                return [ZJ_id]
            if user_id in zx_list_id:
                return [ZJ_id]
            if user_id in zy_list_id:
                return [MZ_id, TJ_id, NJ_id, ZJ_id, FS_id, CY_id]  # 住院
            if user_id in mz_list_id:
                return [TJ_id, NJ_id, ZJ_id, FS_id, CY_id, ZY_id]  # 门诊
            if user_id in zx_list_id:
                return [MZ_id, TJ_id, NJ_id, ZJ_id, FS_id, CY_id, ZY_id]  # 中心药库
            if user_id in tj_list_id:
                return [MZ_id, NJ_id, ZJ_id, FS_id, CY_id, ZY_id]  # 体检药房
            if user_id in nj_list_id:
                return [MZ_id, TJ_id, ZJ_id, FS_id, CY_id, ZY_id]  # 内镜药房
            if user_id in zj_list_id:
                return [MZ_id, TJ_id, NJ_id, FS_id, CY_id, ZY_id]  # 制剂室
            if user_id in fs_list_id:
                return [MZ_id, TJ_id, NJ_id, ZJ_id, CY_id, ZY_id]  # 放射科
            if user_id in cy_list_id:
                return [MZ_id, TJ_id, NJ_id, ZJ_id, FS_id, ZY_id]  # 草药房

    @staticmethod
    def get_days_of_month(year, mon):
        return calendar.monthrange(year, mon)[1]

    @staticmethod
    def getyearandmonth(n=0):
        thisyear = int(year)
        thismon = int(mon)
        totalmon = thismon + n

        if (totalmon <= 12):
            days = str(InternalStraights.get_days_of_month(thisyear, totalmon))
            totalmon = InternalStraights.addzero(totalmon)
            return (year, totalmon, days)
        else:
            i = totalmon / 12
            j = totalmon % 12
            if (j == 0):
                i -= 1
                j = 12
            thisyear += i
            days = str(InternalStraights.get_days_of_month(thisyear, j))
            j = InternalStraights.addzero(j)
            return (str(thisyear), str(j), days)

    @staticmethod
    def addzero(n):
        nabs = abs(int(n))
        if (nabs < 10):
            return "0" + str(nabs)
        else:
            return nabs

    @staticmethod
    def get_today_month(n):
        (y, m, d) = InternalStraights.getyearandmonth(n)
        arr = (y, m, d)
        if (int(day) < int(d)):
            arr = (y, m, day)
        return "-".join("%s" % i for i in arr)







    @staticmethod
    def default_planned_date():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

    @staticmethod
    def default_type():
        return '04'

    @staticmethod
    def default_to_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

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
        return super(InternalStraights, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalStraights, cls).delete(shipments)








class Date_(object):
    @classmethod
    def today(cls):
        pass


class InternalStraightsWizard(Wizard):
    'Internal Straights Wizard'
    __name__ = 'hrp_internal_delivery.internal_straights_wizard'

    start = StateView('hrp_internal_delivery.internal_straights',
                      'hrp_internal_delivery.internal_straights_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', True),
                      ])
    create_ = StateAction('hrp_internal_delivery.act_internal_straights')

    def do_create_(self, action):
        Product = Pool().get('product.product')
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        ShipmentInternal = Pool().get('stock.shipment.internal')
        internal = Pool().get('stock.shipment.internal')
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        lv = {}
        lv['starts'] = data['start']['type']
        lv['company'] = 1
        lv['to_location'] = config.transfers.id  # 中转库存地
        lv['from_location'] = data['start']['from_location']
        lv['place_of_service'] = data['start']['to_location']
        lv['state'] = u'draft'
        Move = data['start']['moves']
        ZY = config.hospital.storage_location.id  # 住院药房
        MZ = config.outpatient_service.storage_location.id  # 门诊药房
        TJ = config.medical.storage_location.id  # 体检药房
        NJ = config.endoscopic.storage_location.id  # 内镜药房
        ZJ = config.preparation.storage_location.id  # 制剂室
        FS = config.ward.storage_location.id  # 放射科
        CY = config.herbs.storage_location.id  # 草药房
        date = time.strftime('%Y%m', time.localtime())
        from_id = data['start']['from_location']
        to_id = data['start']['to_location']
        sequence_dict = {ZY: 'B', MZ: 'X', TJ: 'T', NJ: 'N', ZJ: 'J', FS: 'F', CY: 'C'}
        Keys = sequence_dict.keys()
        if from_id in Keys:
            start_number = sequence_dict[from_id]
        if to_id in Keys:
            end_number = sequence_dict[to_id]
        Start = start_number + end_number
        if len(Start) == 2:
            ShipmentNumber = ShipmentInternal.search([('number', 'like', Start + '%')], order=[["create_date", "DESC"]])
            if ShipmentNumber:
                if int(ShipmentNumber[0].number[2:8]) == int(date):
                    number_sequence = ShipmentNumber[0].number[8:13]
                    number_int = int(number_sequence) + 1
                    EndNumber = str(number_int).zfill(4)
                    NumberSequence = Start + str(date) + str(EndNumber)
                    lv['number'] = NumberSequence
                else:
                    NumberSequence = Start + date + '0001'
                    lv['number'] = NumberSequence
            else:
                NumberSequence = Start + date + '0001'
                lv['number'] = NumberSequence
        else:
            pass
        state = '04'
        list = []
        for each in Move:
            if each['is_collar'] == True:
                dict = {}
                dict['origin'] = None  # each['origin']
                dict['to_location'] = config.transfers.id  # data['start']['to_location']
                dict['product'] = each['product']
                ProductPrice = Product.search([('id', '=', each['product'])])
                dict['cost_price'] = decimal.Decimal(
                    str(float(ProductPrice[0].template.cost_price * decimal.Decimal(str(each['proposal'])))))
                dict['list_price'] = decimal.Decimal(
                    str(float(ProductPrice[0].template.list_price * decimal.Decimal(str(each['proposal'])))))
                dict['from_location'] = data['start']['from_location']
                dict['invoice_lines'] = ()  # each['invoice_lines']
                dict['company'] = 1  # each['company']
                dict['unit_price'] = None  # each['unit_price']产品的价格
                dict['lot'] = None
                dict['starts'] = state
                dict['uom'] = each['uom']
                dict['real_number'] = each['proposal']  # 产品的请领数量
                dict['quantity'] = each['proposal']  # 实发数量
                list.append(dict)
                lv['moves'] = [['create', list]]
                lv['planned_date'] = data['start']['planned_date']
            else:
                pass
        if 'moves' in lv.keys():
            internal.create([lv])
        else:
            pass
        return action, {}
