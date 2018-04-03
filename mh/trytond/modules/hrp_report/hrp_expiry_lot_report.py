# coding:utf-8
import operator
import time
import datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.product import Uom
from trytond.pool import Pool
from trytond.pyson import PYSONEncoder, Eval
from trytond.transaction import Transaction
from trytond.wizard import StateTransition
from trytond.wizard import Wizard, StateView, Button, StateAction
from sql import Literal
from sql.aggregate import Max

__all__ = ['HrpExpiryLotMessageReport', 'HrpExpiryLotContent', 'HrpExpiryLotWizard']


class HrpExpiryLotMessageReport(ModelSQL, ModelView):
    """Hrp Expiry Lot Report Message"""

    __name__ = "hrp_report.hrp_expiry_lot_message_report"

    code = fields.Function(fields.Char('code', select=True), 'get_code')  # 编码
    lot = fields.Char('lot', select=True, readonly=True)  # 批次
    product = fields.Many2One('product.product', 'product', select=True, readonly=True)  # 药品名称
    name = fields.Function(fields.Char('name', select=True), 'get_name')  # 药品名称
    term_of_validity = fields.Date('term_of_validity', select=True, readonly=True)  # 有效期
    frozen = fields.Function(fields.Char('frozen', select=True, readonly=True), 'get_frozen')  # 冻结数量
    frozen_two = fields.Function(fields.Char('frozen_two', select=True, readonly=True), 'get_frozen_two')  # 冻结数量
    unrestricted = fields.Function(fields.Char('unrestricted', select=True, readonly=True), 'get_unrestricted')  # 非限制数量
    unrestricted_two = fields.Function(fields.Char('unrestricted_two', select=True, readonly=True),
                                       'get_unrestricted_two')  # 非限制数量
    drug_specifications = fields.Function(fields.Char('drug_specifications', select=True),
                                          'get_drug_specifications')  # 规格

    @staticmethod
    def table_query(self=None):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        Lot = Pool().get('stock.lot')
        product_lot = Lot.__table__()
        where = Literal(True)
        ProductDrop = Pool().get('product.template')
        Product = Pool().get('product.product')
        UomCategory = Pool().get('product.category')
        con_date = Pool().get('hrp_internal_delivery.internal_straights')
        Date = Pool().get('ir.date')
        today = Date.today()
        start_time = Transaction().context.get('start_time')
        if Transaction().context.get('end_time') != None:
            end_time = Transaction().context.get('end_time')
        else:
            timeStamp = int(time.mktime(time.strptime('5000-01-01', "%Y-%m-%d")))
            rang_date = datetime.datetime.utcfromtimestamp(timeStamp).date()
            end_time = rang_date

        if Transaction().context.get('location'):
            location_id = Transaction().context['location']
            value_none = []
            location_ids = Transaction().context.get('location')
            if location_ids == config.warehouse.storage_location.id:  # 中心药库
                location_frozen_id = config.return_of.id  # 中心药库冻结区
            elif location_ids == config.hospital.storage_location.id:  # 住院药房
                location_frozen_id = config.hospital_freeze.id  # 住院药房冻结区
            elif location_ids == config.outpatient_service.storage_location.id:  # 门诊药房
                location_frozen_id = config.outpatient_freeze.id  # 门诊药房冻结区
            elif location_ids == config.medical.storage_location.id:  # 体检药房
                location_frozen_id = config.medical.freeze_location.id  # 体检药房冻结区
            elif location_ids == config.endoscopic.storage_location.id:  # 内镜药房
                location_frozen_id = config.endoscopic.freeze_location.id  # 内镜药房冻结区
            elif location_ids == config.preparation.storage_location.id:  # 制剂室
                location_frozen_id = config.preparation.freeze_location.id  # 制剂室冻结区
            elif location_ids == config.ward.storage_location.id:  # 放射科
                location_frozen_id = config.ward.freeze_location.id  # 放射科冻结区
            elif location_ids == config.herbs.storage_location.id:  # 草药房
                location_frozen_id = config.herbs.freeze_location.id  # 草药房冻结区
            else:
                location_frozen_id = config.return_of.id  # 药库冻结区
            with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([location_frozen_id], with_childs=True,
                                                               grouping=('product', 'lot'))
                for key, value in warehouse_quant.items():
                    if value > 0.0:
                        if key[-1] != None:
                            product_lots = Lot.search([('id', '=', key[-1])])[0].shelf_life_expiration_date
                            condition = Transaction().context.get('condition')
                            if condition == None:
                                if product_lots >= start_time and product_lots <= end_time:
                                    value_none.append(key[-1])
                            elif condition == '01':
                                get_month = con_date.get_today_month(3)
                                timeStamp = int(time.mktime(time.strptime(get_month, "%Y-%m-%d")))
                                rang_date = datetime.datetime.utcfromtimestamp(timeStamp).date()
                                if product_lots >= start_time and product_lots <= rang_date:
                                    value_none.append(key[-1])
                            elif condition == '02':
                                get_month = con_date.get_today_month(6)
                                timeStamp = int(time.mktime(time.strptime(get_month, "%Y-%m-%d")))
                                rang_date = datetime.datetime.utcfromtimestamp(timeStamp).date()
                                if product_lots >= start_time and product_lots <= rang_date:
                                    value_none.append(key[-1])
                            else:
                                if product_lots <= start_time:
                                    value_none.append(key[-1])
                        else:
                            pass
            with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([location_id], with_childs=True,
                                                               grouping=('product', 'lot'))
                lists = []
                list_lot = []
                product_id = []
                intersection_product = []
                for i in value_none:
                    list_lot.append(i)
                for key, value in warehouse_quant.items():
                    if value > 0.0:
                        if key[-1] != None:
                            product_lots = Lot.search([('id', '=', key[-1])])[0].shelf_life_expiration_date
                            condition = Transaction().context.get('condition')
                            if condition == None:
                                if product_lots >= start_time and product_lots <= end_time:
                                    lists.append(key[-1])
                                    product_id.append(key[1])
                                    list_lot.append(key[-1])
                            if condition == '01':
                                get_month = con_date.get_today_month(3)
                                timeStamp = int(time.mktime(time.strptime(get_month, "%Y-%m-%d")))
                                rang_date = datetime.datetime.utcfromtimestamp(timeStamp).date()
                                if product_lots >= start_time and product_lots <= rang_date:
                                    lists.append(key[-1])
                                    product_id.append(key[1])
                                    list_lot.append(key[-1])
                            if condition == '02':
                                get_month = con_date.get_today_month(6)
                                timeStamp = int(time.mktime(time.strptime(get_month, "%Y-%m-%d")))
                                rang_date = datetime.datetime.utcfromtimestamp(timeStamp).date()
                                if product_lots >= start_time and product_lots <= rang_date:
                                    lists.append(key[-1])
                                    product_id.append(key[1])
                                    list_lot.append(key[-1])
                            if condition == '03':
                                if product_lots <= start_time:
                                    lists.append(key[-1])
                                    product_id.append(key[1])
                                    list_lot.append(key[-1])
                        else:
                            pass

                if Transaction().context.get('drug_type'):  # 通过药品种类进行区分
                    drug_type_id_list = []
                    if Transaction().context['drug_type'] == '00':
                        drug_name = u'西药'
                    elif Transaction().context['drug_type'] == '01':
                        drug_name = u'中成药'
                    elif Transaction().context['drug_type'] == '02':
                        drug_name = u'中草药'
                    elif Transaction().context['drug_type'] == '03':
                        drug_name = u'颗粒中'
                    elif Transaction().context['drug_type'] == '04':
                        drug_name = u'原料药'
                    elif Transaction().context['drug_type'] == '05':
                        drug_name = u'敷药'
                    elif Transaction().context['drug_type'] == '06':
                        drug_name = ''
                    elif Transaction().context['drug_type'] == '07':
                        drug_name = u'同位素'
                    else:
                        drug_name = ''
                    if drug_name == '':
                        pass
                    else:
                        uom_category = UomCategory.search([('name', '=', drug_name)])
                        Drug_type_id = ProductDrop.search([('categories', '=', [uom_category[0].id])])
                        if Drug_type_id:
                            for i in Drug_type_id:
                                intersection_product.append(i)
                                drug_type_id_list.append(i.products[0].id)
                        else:
                            pass
                        intersection_id = [val for val in product_id if val in drug_type_id_list]

                        ids_list = []
                        for ids in intersection_id:
                            find_lot_id = Lot.search([('product', '=', ids)])
                            if find_lot_id:
                                for i in find_lot_id:
                                    ids_list.append(i.id)
                        ggg = [val for val in list_lot if val in ids_list]
                        del list_lot[:]
                        for i in ggg:
                            list_lot.append(i)
                if Transaction().context.get('product'):
                    product_product = []
                    product_ids = Transaction().context.get('product')
                    product_lots = Lot.search([('product', '=', product_ids)])
                    if product_lots:
                        for i in product_lots:
                            product_product.append(i.id)
                        test_lot_id = [val for val in product_product if val in list_lot]
                        del list_lot[:]
                        for i in test_lot_id:
                            list_lot.append(i)
                    if intersection_product == []:
                        pass
                    else:
                        lot_list = []
                        intersection_product_id = [val for val in product_product if val in intersection_product]
                        if intersection_product_id:
                            for ids in intersection_product_id:
                                find_lot_id = Lot.search([('product', '=', ids)])
                                if find_lot_id:
                                    for i in find_lot_id:
                                        lot_list.append(i.id)
                                del list_lot[:]
                                lot_number = [val for val in lot_list if val in list_lot]
                                for i in lot_number:
                                    list_lot.append(i)

                product_lot_all = Lot.search([('id', 'in', list_lot)], query=True, order=[])
                where &= product_lot.id.in_(product_lot_all)
        Result = product_lot.select(
            product_lot.id.as_('id'),
            Max(product_lot.create_uid).as_('create_uid'),
            Max(product_lot.create_date).as_('create_date'),
            Max(product_lot.write_uid).as_('write_uid'),
            Max(product_lot.write_date).as_('write_date'),
            product_lot.number.as_('lot'),
            product_lot.product.as_('product'),
            product_lot.shelf_life_expiration_date.as_('term_of_validity'),
            where=where,
            group_by=product_lot.id)
        return Result

    def get_name(self, name):
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot(self.id)
        product_name = product_lot.product.template.name
        return product_name

    def get_drug_specifications(self, name):
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot(self.id)
        product_name = product_lot.product.drug_specifications
        return product_name

    def get_code(self, name):
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot(self.id)
        product_code = product_lot.product.code
        return product_code

    def get_unrestricted(self, name):
        Date = Pool().get('ir.date')
        today = Date.today()
        ProductUom = Pool().get('product.uom')
        Product = Pool().get('product.product')
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot.search([('id', '=', self.id)])
        product_uom = ProductLot(self.id)
        product_uom = product_uom.product.default_uom.id
        uom = ProductUom.search([('id', '=', product_uom)])
        Uom = uom[0].name
        product_id = product_lot[0].product.id
        location_ids = Transaction().context.get('location')
        with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location_ids], [product_id], with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if value > 0.0:
                    if key[-1] != None:
                        if key[-1] == self.id:
                            return str(value) + Uom
                        else:
                            pass

    def get_unrestricted_two(self, name):
        Date = Pool().get('ir.date')
        today = Date.today()
        Product = Pool().get('product.product')
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot.search([('id', '=', self.id)])
        product_id = product_lot[0].product.id
        product_factor = product_lot[0].product
        location_ids = Transaction().context.get('location')
        with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location_ids], [product_id], with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if value > 0.0:
                    if key[-1] != None:
                        if key[-1] == self.id:
                            factor = Uom.compute_qty(product_factor.default_uom, value,
                                                     product_factor.min_Package, round=True)
                            return str(factor) + product_factor.min_Package.name
                        else:
                            pass

    def get_frozen(self, name):
        Date = Pool().get('ir.date')
        today = Date.today()
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        ProductUom = Pool().get('product.uom')
        Product = Pool().get('product.product')
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot.search([('id', '=', self.id)])
        product_id = product_lot[0].product.id
        product_uom = ProductLot(self.id)
        product_uom = product_uom.product.default_uom.id
        uom = ProductUom.search([('id', '=', product_uom)])
        Uom = uom[0].name
        location_ids = Transaction().context.get('location')
        if location_ids == config.warehouse.storage_location.id:  # 中心药库
            location_frozen_id = config.return_of.id  # 中心药库冻结区
        elif location_ids == config.hospital.storage_location.id:  # 住院药房
            location_frozen_id = config.hospital_freeze.id  # 住院药房冻结区
        elif location_ids == config.outpatient_service.storage_location.id:  # 门诊药房
            location_frozen_id = config.outpatient_freeze.id  # 门诊药房冻结区
        else:
            location_frozen_id = config.return_of.id  # 药库冻结区
        with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location_frozen_id], [product_id], with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if value > 0.0:
                    if key[-1] != None:
                        if key[-1] == self.id:
                            return str(value) + Uom
                        else:
                            pass

    def get_frozen_two(self, name):
        Date = Pool().get('ir.date')
        today = Date.today()
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        Product = Pool().get('product.product')
        ProductLot = Pool().get('stock.lot')
        product_lot = ProductLot.search([('id', '=', self.id)])
        product_id = product_lot[0].product.id
        location_ids = Transaction().context.get('location')
        if location_ids == config.warehouse.storage_location.id:  # 中心药库
            location_frozen_id = config.return_of.id  # 中心药库冻结区
        elif location_ids == config.hospital.storage_location.id:  # 住院药房
            location_frozen_id = config.hospital_freeze.id  # 住院药房冻结区
        elif location_ids == config.outpatient_service.storage_location.id:  # 门诊药房
            location_frozen_id = config.outpatient_freeze.id  # 门诊药房冻结区
        else:
            location_frozen_id = config.return_of.id  # 药库冻结区
        product_factor = product_lot[0].product
        with Transaction().set_context(stock_date_end=today):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location_frozen_id], [product_id], with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if value > 0.0:
                    if key[-1] != None:
                        if key[-1] == self.id:
                            factor = Uom.compute_qty(product_factor.default_uom, value,
                                                     product_factor.min_Package, round=True)
                            return str(factor) + product_factor.min_Package.name
                        else:
                            pass


class HrpExpiryLotContent(ModelView):
    """Hrp Expiry Lot Content"""

    __name__ = 'hrp_report.hrp_expiry_lot_content'

    product = fields.Many2One('product.product', 'product', select=True, depends=['product_location'],
                              domain=[('id', 'in', Eval('product_location'))])  # 药品编码
    product_location = fields.Function(fields.One2Many('product.product', '', 'product_location'),
                                       'on_change_with_product_location')  # 产品检索条件
    # lot = fields.Many2One('stock.lot', 'lot', select=True)  # 批次
    drug_type = fields.Selection([
        ('06', u'全部'),
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('07', u'同位素'),
    ], 'drug_type', select=True, sort=False)  # 药品类型

    start_time = fields.Date('start_time', select=True, readonly=True)  # 时间
    end_time = fields.Date('end_time', select=True)  # 时间

    location = fields.Many2One('stock.location', 'location', select=True)  # 库存地
    condition = fields.Selection([
        ('01', u'三个月'),
        ('02', u'半年'),
        ('03', u'过期'),
    ], 'condition', select=True)  # 毒性级别

    @staticmethod
    def default_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @staticmethod
    def default_start_time():
        Date = Pool().get('ir.date')
        today = str(Date.today())
        return today

    @fields.depends('location', 'start_time')
    def on_change_with_product_location(self):
        if self.location:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            list = []
            with Transaction().set_context(stock_date_end=Date.today()):
                warehouse_quant = Product.products_by_location([self.location], with_childs=True,
                                                               grouping=('product', 'lot'))
                for key in warehouse_quant.items():
                    product_id = key[0][1]
                    list.append(product_id)
            return list


class HrpExpiryLotWizard(Wizard):
    """Hrp Expiry Lot Wizard"""
    __name__ = 'hrp_report.hrp_expiry_lot_wizard'

    start = StateView('hrp_report.hrp_expiry_lot_content',
                      'hrp_report.hrp_expiry_lot_content_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateTransition()
    report = StateAction('hrp_report.act_hrp_expiry_lot_message_report')

    # reports = StateAction('hrp_report.act_hrp_price_profit_loss_message')

    def transition_create_(self):
        if False:
            return 'end'
        else:
            return 'report'

    def do_report(self, action):
        dict = {}
        try:
            self.start.start_time
            dict['start_time'] = self.start.start_time
        except:
            pass
        try:
            self.start.end_time
            dict['end_time'] = self.start.end_time
        except:
            pass
        try:
            self.start.location.id
            dict['location'] = self.start.location.id
        except:
            pass
        try:
            self.start.product.id
            dict['product'] = self.start.product.id
        except:
            pass
        try:
            self.start.drug_type
            dict['drug_type'] = self.start.drug_type
        except:
            pass
        try:
            self.start.condition
            dict['condition'] = self.start.condition
        except:
            pass
        try:
            action['pyson_context'] = PYSONEncoder().encode(dict)
        except:
            pass
        action['name'] += ' - (%s) @ %s' % (u'失效期查询报表', self.start.start_time)
        return action, {}
