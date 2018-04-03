# coding:utf-8
import decimal
import datetime
import time
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Equal, Bool
from trytond.report import Report
from trytond.wizard import StateReport
from trytond.wizard import Wizard, StateView, Button

__all__ = ['InternalQuery', 'InternalQueryWizard', 'InternalDetailed', 'InternalProject', 'ContentInternalProject',
           'QueryDepartmentDone', 'QueryPurchaseDone', 'QueryScrapDone', 'QueryFrozenDone', 'QueryAllocationDone',
           'QueryReturnDone', 'QueryApplyDone', 'GeneralJournal']


class InternalQuery(ModelView):
    """Internal Query"""

    __name__ = 'hrp_internal_delivery.internal_query'
    _rec_name = 'number'

    location = fields.Many2One('stock.location', 'location', readonly=True)  # 所在部门
    location_frozen = fields.Many2One('stock.location', 'location_frozen', readonly=True, states={
        'invisible': True
    })  # 所在部门冻结区
    get_user_warehouse = fields.Many2One('stock.location', 'get_user_warehouse', readonly=True, states={
        'invisible': True
    })
    start_time = fields.Date('start_time')  # 开始时间
    end_time = fields.Date('end_time')  # 结束时间
    number = fields.Char('number')  # 单号
    drug_type = fields.Selection([
        ('西药', u'西药'),
        ('中成药', u'中成药'),
        ('中草药', u'中草药'),
        ('颗粒中', u'颗粒中'),
        ('原料药', u'原料药'),
        ('敷药', u'敷药'),
        ('同位素', u'同位素'),
        ('06', u' '),
    ], 'Starts', select=True)  # 药品类型

    product = fields.Many2One("product.product", "product", domain=[
        ('id', 'in', Eval('product_id'))], depends=['product_id'])
    product_id = fields.Function(
        fields.One2Many('product.product', 'None', 'product_id', depends=['product_id', 'drug_type']),
        'on_change_with_product_id')

    detailed_project = fields.Selection([
        ('detailed_query', u'明细查询'),
        ('project_query', u'项目查询')
    ], 'detailed_project', select=True)  # 查询类别

    detailed_query = fields.Boolean('detailed_query', states={
        'readonly': Bool(Eval('move_query_apply')) | Bool(Eval('move_query_return')) | Bool(
            Eval('move_query_allocation')) | Bool(Eval('move_query_frozen')) | Bool(Eval('move_query_scrap')) | Bool(
            Eval('move_query_purchase')) | Bool(Eval('move_query_department')) | Bool(Eval('move_project'))
    })  # 明细查询
    project_query = fields.Boolean('project_query', states={
        'readonly': Bool(Eval('move_query_apply')) | Bool(Eval('move_query_return')) | Bool(
            Eval('move_query_allocation')) | Bool(Eval('move_query_frozen')) | Bool(Eval('move_query_scrap')) | Bool(
            Eval('move_query_purchase')) | Bool(Eval('move_query_department')) | Bool(Eval('move_project'))
    })  # 项目查询
    document_type = fields.Selection([
        ('00', u'请领单'),
        ('01', u'请退单'),
        ('02', u'调拨出库'),
        ('03', u'调拨入库'),
        ('04', u'冻结转非限制'),
        ('05', u'非限制转冻结'),
        ('06', u'报损单'),
        ('07', u'无采购订单'),
        ('08', u'科室领药单'),
    ], 'document_type', select=True, sort=False)  # 单据类型

    message_find = fields.Boolean('message_find')  # 查找

    move_detailed = fields.One2Many('hrp_internal_delivery.internal_detailed', 'None', 'move_detailed', states={
        'invisible': ~Bool(Eval('detailed_query'))
    })  # 明细表
    move_project = fields.One2Many('hrp_internal_delivery.internal_project', 'None', 'move_project', states={
        'invisible': ~Equal(Eval('detailed_project'), 'project_query')
    }, domain=[
        ('document_type', '=', Eval('document_type')),
        ('detailed_project', '=', Eval('detailed_project')),
    ], depends=['detailed_project', 'document_type'])  # 项目表

    move_query_apply = fields.One2Many('hrp_internal_delivery.query_apply_done', 'None', 'move_query_apply', states={
        'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'), '00')
    }, depends=['detailed_project', 'document_type'])  # 请领

    move_query_return = fields.One2Many('hrp_internal_delivery.query_return_done', 'None', 'move_query_return', states={
        'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'), '01')
    }, depends=['detailed_project', 'document_type'])  # 请退

    move_query_allocation = fields.One2Many('hrp_internal_delivery.query_allocation_done', 'None',
                                            'move_query_allocation', states={
            'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'),
                                                                                     '02') & ~Equal(
                Eval('document_type'), '03')
        }, depends=['detailed_project', 'document_type'])  # 内部调拨

    move_query_frozen = fields.One2Many('hrp_internal_delivery.query_frozen_done', 'None', 'move_query_frozen', states={
        'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'), '04') & ~Equal(
            Eval('document_type'), '05')
    }, depends=['detailed_project', 'document_type'])  # 不合格

    move_query_scrap = fields.One2Many('hrp_internal_delivery.query_scrap_done', 'None', 'move_query_scrap', states={
        'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'), '06')
    }, depends=['detailed_project', 'document_type'])  # 报废

    move_query_purchase = fields.One2Many('hrp_internal_delivery.query_purchase_done', 'None', 'move_query_purchase',
                                          states={
                                              'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(
                                                  Eval('document_type'), '07')
                                          }, depends=['detailed_project', 'document_type'])  # 无采购

    move_query_department = fields.One2Many('hrp_internal_delivery.query_department_done', 'None',
                                            'move_query_department', states={
            'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(Eval('document_type'), '08')
        }, depends=['detailed_project', 'document_type'])  # 科室领药单

    @fields.depends('drug_type', 'product_id')
    def on_change_with_product_id(self):
        UomCategory = Pool().get('product.category')
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        product = Pool().get('product.product')
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        location_id = UserId.get_user_id()
        list_id = []
        if location_id == config.warehouse.storage_location.id:
            if self.drug_type == '06':
                Product = product.search([])
                for i in Product:
                    list_id.append(i.id)
            else:
                uom_category = UomCategory.search([('name', '=', self.drug_type)])
                categories_id = uom_category[0].id
                Product = product.search([
                    ('categories', '=', categories_id),
                    ('is_direct_sending', '=', False),
                ])
                for i in Product:
                    list_id.append(i.id)
        else:
            if self.drug_type == '06':
                Product = product.search([])
                for i in Product:
                    list_id.append(i.id)
            else:
                uom_category = UomCategory.search([('name', '=', self.drug_type)])
                if uom_category:
                    categories_id = uom_category[0].id
                    Product = product.search([
                        ('categories', '=', categories_id),
                        ('is_direct_sending', '=', False),
                    ])
                    for i in Product:
                        list_id.append(i.id)
        return list_id

    @staticmethod
    def default_drug_type():
        return '06'

    @staticmethod
    def default_start_time():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_end_time():
        Date = Pool().get('ir.date')
        return Date.today()

    @fields.depends('detailed_project', 'get_user_warehouse', 'project_query', 'detailed_query', 'move_project',
                    'location_frozen', 'document_type', 'location', 'number', 'product', 'drug_type', 'end_time',
                    'start_time', 'move_query_apply', 'message_find', 'move_query_return', 'move_query_allocation',
                    'move_query_frozen', 'move_query_scrap', 'move_query_purchase', 'move_query_department')
    def on_change_message_find(self):
        UomCategory = Pool().get('product.category')
        internal = Pool().get('stock.shipment.internal')
        Move = Pool().get('stock.move')
        condition = []
        scrap = []
        library = [('state', '=', 'done')]
        storage = [('state', '=', 'done')]
        consume = [('state', '=', 'done')]
        return_drug = [('state', '=', 'done')]
        move_condition = []
        if self.message_find == True:
            tim = str(self.end_time)
            timeArray = time.strptime(tim, "%Y-%m-%d")
            timeStamp = int(time.mktime(timeArray)) + 86400
            timeArray = time.localtime(timeStamp)
            otherStyleTime = time.strftime("%Y-%m-%d", timeArray)

            if self.detailed_project == 'detailed_query':
                if self.start_time != None:
                    condition.append(('effective_date', '>=', self.start_time))
                    move_condition.append(('effective_date', '>=', self.start_time))
                    scrap.append(('create_date', '>=', datetime.datetime.strptime(str(self.start_time), '%Y-%m-%d')))
                    library.append(('effective_date', '>=', self.start_time))
                    storage.append(('effective_date', '>=', self.start_time))
                    consume.append(('create_date', '>=', datetime.datetime.strptime(str(self.start_time), '%Y-%m-%d')))
                    return_drug.append(('effective_date', '>=', self.start_time))
                if self.end_time != None:
                    condition.append(('effective_date', '<=', self.end_time))
                    move_condition.append(('effective_date', '<=', self.end_time))
                    scrap.append(('create_date', '<=', datetime.datetime.strptime(otherStyleTime, '%Y-%m-%d')))
                    library.append(('effective_date', '<=', self.end_time))
                    storage.append(('effective_date', '<=', self.end_time))
                    consume.append(('create_date', '<=', datetime.datetime.strptime(otherStyleTime, '%Y-%m-%d')))
                    return_drug.append(('effective_date', '<=', self.end_time))
                if self.number != u'':
                    condition.append(('number', '=', self.number))
                    move_condition.append(('number', '=', self.number))
                    scrap.append(('number', '=', self.number))
                    library.append(('number', '=', self.number))
                    storage.append(('number', '=', self.number))
                    consume.append(('number', '=', self.number))
                    return_drug.append(('number', '=', self.number))
                if self.document_type == '00':  # 请领单
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', 'in', ['00', '06']))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '01':  # 请退单
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '01'))
                    # condition.append(('from_location', '=', self.location_frozen))
                if self.document_type == '02':  # 内部调拨出库
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '04'))
                    condition.append(('from_location', '=', self.location))
                if self.document_type == '03':  # 内部调拨入库
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '04'))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '04':  # 冻结转非限制
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '03'))
                    condition.append(('from_location', '=', self.location_frozen))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '05':  # 非限制转冻结
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '02'))
                    condition.append(('from_location', '=', self.location))
                    condition.append(('to_location', '=', self.location_frozen))
                if self.product != None:
                    scrap.append(('product', '=', self.product))
                    Internal = internal.search(condition)
                    if Internal:
                        lists = []
                        product_id = self.product.id
                        for each in Internal:
                            move_list_id = []
                            move_line = each.moves
                            move_id = []
                            for i in move_line:
                                if self.drug_type == None:
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_list_id.append(dict_move)
                                elif self.drug_type == '06':
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_list_id.append(dict_move)
                                else:
                                    categories = [cate.id for cate in i.product.categories][0]
                                    uom_category = UomCategory.search([('id', '=', categories)])
                                    uom_name = uom_category[0].name
                                    if self.drug_type == uom_name:
                                        dict_move = {}
                                        dict_move[i.product.id] = i.id
                                        move_list_id.append(dict_move)
                                    else:
                                        pass
                            for move_each in move_list_id:
                                if move_each.keys()[0] != product_id:
                                    pass
                                else:
                                    move_id.append(move_each[product_id])
                            message_list = []
                            for i in move_id:
                                message_move = Move.search([('id', '=', i)])
                                if message_move:
                                    for message in message_move:
                                        message_dict = {}
                                        message_dict['product'] = message.product.name
                                        message_dict['code'] = message.product.code
                                        message_dict['company'] = message.uom
                                        message_dict['lot'] = str(message.lot.number)
                                        message_dict['time'] = str(message.lot.shelf_life_expiration_date)
                                        if message.real_number == None:
                                            message_dict['odd_numbers'] = ''
                                        else:
                                            if self.document_type == '01':
                                                message_dict['odd_numbers'] = '-' + str(message.real_number)
                                            else:
                                                message_dict['odd_numbers'] = str(message.real_number)
                                        if self.document_type == '01':
                                            message_dict['proposal'] = '-' + str(message.quantity)
                                        else:
                                            message_dict['proposal'] = str(message.quantity)
                                        message_dict['drug_specifications'] = str(
                                            message.product.template.drug_specifications)
                                        message_list.append(message_dict)
                            if message_list == []:
                                pass
                            else:
                                if self.document_type == '02':
                                    message_list[-1]['number'] = str(each.number)
                                    message_list[-1]['processing_time'] = str(each.effective_date)
                                else:
                                    message_list[0]['number'] = str(each.number)
                                    message_list[0]['processing_time'] = str(each.effective_date)
                            if self.document_type == '02':
                                message_lists = sorted(message_list, key=lambda x: (x['odd_numbers']), reverse=True)

                                for i in message_lists:
                                    lists.append(i)
                            else:
                                for i in message_list:
                                    lists.append(i)

                        if self.document_type == '00':
                            self.move_query_apply = lists
                        if self.document_type == '01':
                            self.move_query_return = lists
                        if self.document_type == '02':
                            self.move_query_allocation = lists
                        if self.document_type == '03':
                            self.move_query_allocation = lists
                        if self.document_type == '04':
                            self.move_query_frozen = lists
                        if self.document_type == '05':
                            self.move_query_frozen = lists
                        if self.document_type == '06':
                            self.move_query_scrap = []
                        if self.document_type == '07':
                            self.move_query_purchase = []
                        if self.document_type == '08':
                            self.move_query_department = []
                else:
                    Internal = internal.search(condition)
                    if Internal:
                        lists = []
                        for each in Internal:
                            moves_content = []
                            move_line = each.moves
                            for i in move_line:
                                if self.drug_type == None:
                                    move_dict = {}
                                    move_dict['product'] = i.product.name
                                    move_dict['code'] = i.product.code
                                    move_dict['additional'] = i.product.template.attach
                                    move_dict['cost_price'] = i.cost_price
                                    move_dict['list_price'] = i.list_price
                                    try:
                                        i.lot.number
                                        move_dict['lot'] = str(i.lot.number)
                                    except:
                                        pass
                                    try:
                                        i.lot.shelf_life_expiration_date
                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                    except:
                                        pass
                                    move_dict['company'] = i.uom
                                    if i.real_number == None:
                                        move_dict['odd_numbers'] = ''
                                    else:
                                        if self.document_type == '01':
                                            move_dict['odd_numbers'] = '-' + str(i.real_number)
                                        else:
                                            move_dict['odd_numbers'] = str(i.real_number)
                                    if self.document_type == '01':
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                    else:
                                        move_dict['proposal'] = str(i.quantity)
                                    move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                    moves_content.append(move_dict)
                                elif self.drug_type == '06':
                                    move_dict = {}
                                    move_dict['product'] = i.product.name
                                    move_dict['code'] = i.product.code
                                    move_dict['additional'] = i.product.template.attach
                                    move_dict['cost_price'] = i.cost_price
                                    move_dict['list_price'] = i.list_price
                                    try:
                                        i.lot.number
                                        move_dict['lot'] = str(i.lot.number)
                                    except:
                                        pass
                                    try:
                                        i.lot.shelf_life_expiration_date
                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                    except:
                                        pass
                                    move_dict['company'] = i.uom
                                    if i.real_number == None:
                                        move_dict['odd_numbers'] = ''
                                    else:
                                        if self.document_type == '01':
                                            move_dict['odd_numbers'] = '-' + str(i.real_number)
                                        else:
                                            move_dict['odd_numbers'] = str(i.real_number)
                                    if self.document_type == '01':
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                    else:
                                        move_dict['proposal'] = str(i.quantity)
                                    move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                    moves_content.append(move_dict)
                                else:
                                    move_dict = {}
                                    categories = [cate.id for cate in i.product.categories][0]
                                    uom_category = UomCategory.search([('id', '=', categories)])
                                    uom_name = uom_category[0].name
                                    if self.drug_type == uom_name:
                                        move_dict['product'] = i.product.name
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        move_dict['cost_price'] = i.cost_price
                                        move_dict['list_price'] = i.list_price
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        if i.real_number == None:
                                            move_dict['odd_numbers'] = ''
                                        else:
                                            if self.document_type == '01':
                                                move_dict['odd_numbers'] = '-' + str(i.real_number)
                                            else:
                                                move_dict['odd_numbers'] = str(i.real_number)
                                        if self.document_type == '01':
                                            move_dict['proposal'] = '-' + str(i.quantity)
                                        else:
                                            move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        moves_content.append(move_dict)
                                    else:
                                        pass
                            if moves_content == []:
                                pass
                            else:
                                if self.document_type == '02':
                                    moves_content[-1]['number'] = str(each.number)
                                    moves_content[-1]['processing_time'] = str(each.effective_date)
                                else:
                                    moves_content[0]['number'] = str(each.number)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                            if self.document_type == '02':
                                moves_contents = sorted(moves_content, key=lambda x: (x['odd_numbers']), reverse=True)
                                for i in moves_contents:
                                    lists.append(i)
                            else:
                                for i in moves_content:
                                    lists.append(i)
                        if self.document_type == '00':
                            self.move_query_apply = lists
                        if self.document_type == '01':
                            self.move_query_return = lists
                        if self.document_type == '02':
                            self.move_query_allocation = lists
                        if self.document_type == '03':
                            self.move_query_allocation = lists
                        if self.document_type == '04':
                            self.move_query_frozen = lists
                        if self.document_type == '05':
                            self.move_query_frozen = lists
                        if self.document_type == '06':
                            self.move_query_scrap = []
                        if self.document_type == '07':
                            self.move_query_purchase = []
                        if self.document_type == '08':
                            self.move_query_department = []
                if self.document_type == '06':  # 报损单
                    location_id = []
                    location_id.append(self.location)
                    location_id.append(self.location_frozen)
                    User = Pool().get('res.user')
                    scrap_list = Pool().get('hrp_caustic_excessive_storage')
                    scrap.append(('location', 'in', location_id))
                    Scrap = scrap_list.search(scrap)
                    result_scrap = []
                    for each in Scrap:
                        if each.write_date == None:
                            write_time = ''
                        else:
                            write_time = each.write_date.strftime('%Y-%m-%d')
                        if each.create_uid == None:
                            create_user = ''
                        else:
                            create_uid = each.create_uid.id
                            create_user = User.search(['id', '=', create_uid])[0].name
                        if each.write_uid == None:
                            write_user = ''
                        else:
                            write_uid = each.write_uid.id
                            write_user = User.search(['id', '=', write_uid])[0].name

                        if self.drug_type == None:
                            dict = {}
                            if each.state == 'assigned':
                                dict['write_user'] = ''
                                dict['write_time'] = ''
                            else:
                                dict['write_user'] = write_user
                                dict['write_time'] = write_time
                            dict['state'] = each.state
                            dict['why'] = each.why
                            dict['create_user'] = create_user

                            dict['number'] = str(each.return_shipment.number)
                            dict['processing_time'] = str(each.create_date).split(' ')[0]
                            dict['product'] = each.product.template.name
                            dict['company'] = each.retail_package
                            if each.shipment_internal == None:
                                pass
                            else:
                                for i in each.shipment_internal.moves:
                                    if i.product == each.product:
                                        if i.list_price == None:
                                            pass
                                        else:
                                            dict['list_price'] = decimal.Decimal(decimal.Decimal(
                                                str(i.list_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                decimal.Decimal('0.00'))
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            dict['cost_price'] = decimal.Decimal(decimal.Decimal(
                                                str(i.cost_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                decimal.Decimal('0.00'))
                            dict['code'] = each.product.code
                            dict['additional'] = each.product.template.attach
                            dict['drug_specifications'] = str(each.product.template.drug_specifications)
                            dict['lot'] = str(each.lot.number)
                            dict['time'] = str(each.lot.shelf_life_expiration_date)
                            if each.type == 'excessive':
                                dict['proposal'] = '-' + str(each.quantity)
                            else:
                                dict['proposal'] = str(each.quantity)
                            result_scrap.append(dict)
                        elif self.drug_type == '06':
                            dict = {}
                            dict['state'] = each.state
                            if each.state == 'assigned':
                                dict['write_user'] = ''
                                dict['write_time'] = ''
                            else:
                                dict['write_user'] = write_user
                                dict['write_time'] = write_time
                            dict['why'] = each.why
                            dict['create_user'] = create_user

                            dict['number'] = str(each.return_shipment.number)
                            dict['processing_time'] = str(each.create_date).split(' ')[0]
                            dict['product'] = each.product.template.name
                            dict['company'] = each.retail_package
                            if each.shipment_internal == None:
                                pass
                            else:
                                for i in each.shipment_internal.moves:
                                    if i.product == each.product:
                                        if i.list_price == None:
                                            pass
                                        else:
                                            dict['list_price'] = decimal.Decimal(decimal.Decimal(
                                                str(i.list_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                decimal.Decimal('0.00'))
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            dict['cost_price'] = decimal.Decimal(decimal.Decimal(
                                                str(i.cost_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                decimal.Decimal('0.00'))
                            dict['code'] = each.product.code
                            dict['additional'] = each.product.template.attach
                            dict['drug_specifications'] = str(each.product.template.drug_specifications)
                            dict['lot'] = str(each.lot.number)
                            dict['time'] = str(each.lot.shelf_life_expiration_date)
                            if each.type == 'excessive':
                                dict['proposal'] = '-' + str(each.quantity)
                            else:
                                dict['proposal'] = str(each.quantity)
                            result_scrap.append(dict)
                        else:
                            categories = [cate.id for cate in each.product.categories][0]
                            uom_category = UomCategory.search([('id', '=', categories)])
                            uom_name = uom_category[0].name
                            if self.drug_type == uom_name:
                                dict = {}
                                dict['state'] = each.state
                                if each.state == 'assigned':
                                    dict['write_user'] = ''
                                    dict['write_time'] = ''
                                else:
                                    dict['write_user'] = write_user
                                    dict['write_time'] = write_time
                                dict['why'] = each.why
                                dict['create_user'] = create_user

                                dict['number'] = str(each.return_shipment.number)
                                dict['processing_time'] = str(each.create_date).split(' ')[0]
                                dict['product'] = each.product.template.name
                                dict['company'] = each.retail_package
                                if each.shipment_internal == None:
                                    pass
                                else:
                                    for i in each.shipment_internal.moves:
                                        if i.product == each.product:
                                            if i.list_price == None:
                                                pass
                                            else:
                                                dict['list_price'] = decimal.Decimal(decimal.Decimal(
                                                    str(i.list_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                    decimal.Decimal('0.00'))
                                            if i.cost_price == None:
                                                pass
                                            else:
                                                dict['cost_price'] = decimal.Decimal(decimal.Decimal(
                                                    str(i.cost_price * decimal.Decimal(str(each.quantity))))).quantize(
                                                    decimal.Decimal('0.00'))
                                dict['code'] = each.product.code
                                dict['additional'] = each.product.template.attach
                                dict['drug_specifications'] = str(each.product.template.drug_specifications)
                                dict['lot'] = str(each.lot.number)
                                dict['time'] = str(each.lot.shelf_life_expiration_date)
                                if each.type == 'excessive':
                                    dict['proposal'] = '-' + str(each.quantity)
                                else:
                                    dict['proposal'] = str(each.quantity)
                                result_scrap.append(dict)
                            else:
                                pass
                    finnaly = sorted(result_scrap, key=lambda x: (x['processing_time']), reverse=True)
                    # finnaly = sorted(result_scrap, key=operator.itemgetter('processing_time'))
                    self.move_query_scrap = finnaly
                if self.document_type == '07':  # 无采购订单出入库
                    library_location = Pool().get('stock.shipment.in.return')  # 出库
                    storage_location = Pool().get('stock.shipment.in')  # 入库
                    Library = library_location.search(library)
                    lists = []
                    number_sequence = 0
                    for each in Library:
                        number_sequence += 1
                        if each.from_location == self.get_user_warehouse or self.location_frozen:
                            moves_content = []
                            move_line = each.moves
                            if self.product != None:
                                move_purchase_id = []
                                list_purchase_id = []
                                for i in move_line:
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_purchase_id.append(dict_move)
                                    for move_each in move_purchase_id:
                                        if move_each.keys()[0] != product_id:
                                            pass
                                        else:
                                            list_purchase_id.append(move_each[product_id])
                                for i in list_purchase_id:
                                    message_move = Move.search([('id', '=', i)])
                                    if message_move:
                                        moves_purchase_content = []
                                        for i in message_move:
                                            if self.drug_type == None:
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = -i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = -i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = '—' + str(i.quantity)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.from_location == self.location:
                                                    moves_purchase_content.append(move_dict)
                                            elif self.drug_type == '06':
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = -i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = -i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = '—' + str(i.quantity)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.from_location == self.location:
                                                    moves_purchase_content.append(move_dict)
                                            else:
                                                categories = [cate.id for cate in i.product.categories][0]
                                                uom_category = UomCategory.search([('id', '=', categories)])
                                                uom_name = uom_category[0].name
                                                if self.drug_type == uom_name:
                                                    move_dict = {}
                                                    move_dict['product'] = i.product.name
                                                    if i.list_price == None:
                                                        pass
                                                    else:
                                                        move_dict['list_price'] = -i.list_price
                                                    if i.cost_price == None:
                                                        pass
                                                    else:
                                                        move_dict['cost_price'] = -i.cost_price
                                                    move_dict['code'] = i.product.code
                                                    move_dict['additional'] = i.product.template.attach
                                                    try:
                                                        i.lot.number
                                                        move_dict['lot'] = str(i.lot.number)
                                                    except:
                                                        pass
                                                    try:
                                                        i.lot.shelf_life_expiration_date
                                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                    except:
                                                        pass
                                                    move_dict['company'] = i.uom
                                                    move_dict['effective_date'] = str(each.effective_date)
                                                    move_dict['odd_numbers'] = str(i.real_number)
                                                    move_dict['proposal'] = '—' + str(i.quantity)
                                                    move_dict['drug_specifications'] = str(
                                                        i.product.template.drug_specifications)
                                                    if i.from_location == self.location:
                                                        moves_purchase_content.append(move_dict)
                                                else:
                                                    pass
                                    if moves_purchase_content == []:
                                        pass
                                    else:
                                        moves_purchase_content[0]['number'] = str(number_sequence)
                                        moves_purchase_content[0]['processing_time'] = str(each.effective_date)
                                    for i in moves_purchase_content:
                                        lists.append(i)
                            else:
                                for i in move_line:
                                    if self.drug_type == None:
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = -i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = -i.cost_price
                                        move_dict['product'] = i.product.name
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        moves_content.append(move_dict)
                                    elif self.drug_type == '06':
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = -i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = -i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = '—' + str(i.quantity)
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        moves_content.append(move_dict)
                                    else:
                                        categories = [cate.id for cate in i.product.categories][0]
                                        uom_category = UomCategory.search([('id', '=', categories)])
                                        uom_name = uom_category[0].name
                                        if self.drug_type == uom_name:
                                            move_dict = {}
                                            move_dict['product'] = i.product.name
                                            if i.list_price == None:
                                                pass
                                            else:
                                                move_dict['list_price'] = -i.list_price
                                            if i.cost_price == None:
                                                pass
                                            else:
                                                move_dict['cost_price'] = -i.cost_price
                                            move_dict['code'] = i.product.code
                                            move_dict['additional'] = i.product.template.attach
                                            try:
                                                i.lot.number
                                                move_dict['lot'] = str(i.lot.number)
                                            except:
                                                pass
                                            try:
                                                i.lot.shelf_life_expiration_date
                                                move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                            except:
                                                pass
                                            move_dict['company'] = i.uom
                                            move_dict['effective_date'] = str(each.effective_date)
                                            move_dict['odd_numbers'] = str(i.real_number)
                                            move_dict['proposal'] = '—' + str(i.quantity)
                                            move_dict['drug_specifications'] = str(
                                                i.product.template.drug_specifications)
                                            moves_content.append(move_dict)
                                        else:
                                            pass
                                if moves_content == []:
                                    pass
                                else:
                                    moves_content[0]['number'] = str(number_sequence)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                                for i in moves_content:
                                    lists.append(i)

                    Storage = storage_location.search(storage)
                    for each in Storage:
                        number_sequence += 1
                        if each.warehouse == self.get_user_warehouse:
                            moves_content = []
                            move_line = each.moves
                            if self.product != None:
                                move_purchase_id = []
                                list_purchase_id = []
                                for i in move_line:
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_purchase_id.append(dict_move)
                                    for move_each in move_purchase_id:
                                        if move_each.keys()[0] != product_id:
                                            pass
                                        else:
                                            list_purchase_id.append(move_each[product_id])
                                for i in list_purchase_id:
                                    message_move = Move.search([('id', '=', i)])
                                    if message_move:
                                        moves_purchase_content = []
                                        for i in message_move:
                                            if self.drug_type == None:
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = str(i.quantity)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.to_location != self.location:
                                                    moves_purchase_content.append(move_dict)
                                            elif self.drug_type == '06':
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = str(i.quantity)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.to_location != self.location:
                                                    moves_purchase_content.append(move_dict)
                                            else:
                                                categories = [cate.id for cate in i.product.categories][0]
                                                uom_category = UomCategory.search([('id', '=', categories)])
                                                uom_name = uom_category[0].name
                                                if self.drug_type == uom_name:
                                                    move_dict = {}
                                                    move_dict['product'] = i.product.name
                                                    if i.list_price == None:
                                                        pass
                                                    else:
                                                        move_dict['list_price'] = i.list_price
                                                    if i.cost_price == None:
                                                        pass
                                                    else:
                                                        move_dict['cost_price'] = i.cost_price
                                                    move_dict['code'] = i.product.code
                                                    move_dict['additional'] = i.product.template.attach
                                                    try:
                                                        i.lot.number
                                                        move_dict['lot'] = str(i.lot.number)
                                                    except:
                                                        pass
                                                    try:
                                                        i.lot.shelf_life_expiration_date
                                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                    except:
                                                        pass
                                                    move_dict['company'] = i.uom
                                                    move_dict['effective_date'] = str(each.effective_date)
                                                    move_dict['odd_numbers'] = str(i.real_number)
                                                    move_dict['proposal'] = str(i.quantity)
                                                    move_dict['drug_specifications'] = str(
                                                        i.product.template.drug_specifications)
                                                    if i.to_location != self.location:
                                                        moves_purchase_content.append(move_dict)
                                                else:
                                                    pass
                                    if moves_purchase_content == []:
                                        pass
                                    else:
                                        moves_purchase_content[0]['number'] = str(number_sequence)
                                        moves_purchase_content[0]['processing_time'] = str(each.effective_date)
                                    for i in moves_purchase_content:
                                        lists.append(i)
                            else:
                                for i in move_line:
                                    if self.drug_type == None:
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_specifications'] = str(
                                            i.product.template.drug_specifications)
                                        if i.to_location != self.location:
                                            moves_content.append(move_dict)
                                    elif self.drug_type == '06':
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_specifications'] = str(
                                            i.product.template.drug_specifications)
                                        if i.to_location != self.location:
                                            moves_content.append(move_dict)
                                    else:
                                        categories = [cate.id for cate in i.product.categories][0]
                                        uom_category = UomCategory.search([('id', '=', categories)])
                                        uom_name = uom_category[0].name
                                        if self.drug_type == uom_name:
                                            move_dict = {}
                                            move_dict['product'] = i.product.name
                                            if i.list_price == None:
                                                pass
                                            else:
                                                move_dict['list_price'] = i.list_price
                                            if i.cost_price == None:
                                                pass
                                            else:
                                                move_dict['cost_price'] = i.cost_price
                                            move_dict['code'] = i.product.code
                                            move_dict['additional'] = i.product.template.attach
                                            try:
                                                i.lot.number
                                                move_dict['lot'] = str(i.lot.number)
                                            except:
                                                pass
                                            try:
                                                i.lot.shelf_life_expiration_date
                                                move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                            except:
                                                pass
                                            move_dict['company'] = i.uom
                                            move_dict['effective_date'] = str(each.effective_date)
                                            move_dict['odd_numbers'] = str(i.real_number)
                                            move_dict['proposal'] = str(i.quantity)
                                            move_dict['drug_specifications'] = str(
                                                i.product.template.drug_specifications)
                                            if i.to_location != self.location:
                                                moves_content.append(move_dict)
                                        else:
                                            pass
                                if moves_content == []:
                                    pass
                                else:
                                    moves_content[0]['number'] = str(number_sequence)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                                for i in moves_content:
                                    lists.append(i)
                    finnaly_list = sorted(lists, key=lambda x: (x['effective_date']), reverse=True)
                    self.move_query_purchase = finnaly_list

                if self.document_type == '08':  # 科室领药单
                    consume_product = Pool().get('stock.shipment.out.return')  # 科室退药
                    return_product = Pool().get('stock.shipment.out')  # 科室消耗
                    Consume = consume_product.search(consume)
                    lists = []
                    for each in Consume:
                        if each.warehouse == self.get_user_warehouse:
                            moves_content = []
                            move_line = each.moves
                            # if each.move_type == 'Z07' or each.move_type == 'Z08':
                            if self.product != None:
                                move_purchase_id = []
                                list_purchase_id = []
                                for i in move_line:
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_purchase_id.append(dict_move)
                                    for move_each in move_purchase_id:
                                        if move_each.keys()[0] != product_id:
                                            pass
                                        else:
                                            list_purchase_id.append(move_each[product_id])
                                for i in list_purchase_id:
                                    message_move = Move.search([('id', '=', i)])
                                    if message_move:
                                        moves_purchase_content = []
                                        for i in message_move:
                                            if self.drug_type == None:
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = -i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = -i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = '-' + str(i.quantity)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                move_dict['drug_receiving_section'] = each.party.name
                                                move_dict['drug_receiving_code'] = each.party.code
                                                if i.to_location == self.location:
                                                    moves_purchase_content.append(move_dict)
                                                else:
                                                    pass
                                            elif self.drug_type == '06':
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = -i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = -i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = '-' + str(i.quantity)
                                                move_dict['drug_receiving_section'] = each.customer.name
                                                move_dict['drug_receiving_code'] = each.customer.code
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.to_location == self.location:
                                                    moves_purchase_content.append(move_dict)
                                                else:
                                                    pass
                                            else:
                                                categories = [cate.id for cate in i.product.categories][0]
                                                uom_category = UomCategory.search([('id', '=', categories)])
                                                uom_name = uom_category[0].name
                                                if self.drug_type == uom_name:
                                                    move_dict = {}
                                                    move_dict['product'] = i.product.name
                                                    if i.list_price == None:
                                                        pass
                                                    else:
                                                        move_dict['list_price'] = -i.list_price
                                                    if i.cost_price == None:
                                                        pass
                                                    else:
                                                        move_dict['cost_price'] = -i.cost_price
                                                    move_dict['code'] = i.product.code
                                                    move_dict['additional'] = i.product.template.attach
                                                    try:
                                                        i.lot.number
                                                        move_dict['lot'] = str(i.lot.number)
                                                    except:
                                                        pass
                                                    try:
                                                        i.lot.shelf_life_expiration_date
                                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                    except:
                                                        pass
                                                    move_dict['company'] = i.uom
                                                    move_dict['effective_date'] = str(each.effective_date)
                                                    move_dict['odd_numbers'] = str(i.real_number)
                                                    move_dict['proposal'] = '-' + str(i.quantity)
                                                    move_dict['drug_receiving_section'] = each.customer.name
                                                    move_dict['drug_receiving_code'] = each.customer.code
                                                    move_dict['drug_specifications'] = str(
                                                        i.product.template.drug_specifications)
                                                    if i.to_location == self.location:
                                                        moves_purchase_content.append(move_dict)
                                                    else:
                                                        pass
                                                else:
                                                    pass
                                    if moves_purchase_content == []:
                                        pass
                                    else:
                                        moves_purchase_content[0]['number'] = str(each.number)
                                        moves_purchase_content[0]['processing_time'] = str(each.effective_date)
                                    for i in moves_purchase_content:
                                        lists.append(i)
                            else:
                                for i in move_line:
                                    if self.drug_type == None:
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = -i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = -i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                        move_dict['drug_receiving_section'] = each.customer.name
                                        move_dict['drug_receiving_code'] = each.customer.code
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        if i.to_location != self.location:
                                            moves_content.append(move_dict)
                                        else:
                                            pass
                                    elif self.drug_type == '06':
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = -i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = -i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                        move_dict['drug_receiving_section'] = each.customer.name
                                        move_dict['drug_receiving_code'] = each.customer.code
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        if i.to_location == self.location:
                                            moves_content.append(move_dict)
                                    else:
                                        categories = [cate.id for cate in i.product.categories][0]
                                        uom_category = UomCategory.search([('id', '=', categories)])
                                        uom_name = uom_category[0].name
                                        if self.drug_type == uom_name:
                                            move_dict = {}
                                            move_dict['product'] = i.product.name
                                            move_dict['code'] = i.product.code
                                            move_dict['additional'] = i.product.template.attach
                                            try:
                                                i.lot.number
                                                move_dict['lot'] = str(i.lot.number)
                                            except:
                                                pass
                                            try:
                                                i.lot.shelf_life_expiration_date
                                                move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                            except:
                                                pass
                                            move_dict['company'] = i.uom
                                            move_dict['effective_date'] = str(each.effective_date)
                                            move_dict['odd_numbers'] = str(i.real_number)
                                            move_dict['proposal'] = '-' + str(i.quantity)
                                            move_dict['drug_receiving_section'] = each.customer.name
                                            move_dict['drug_receiving_code'] = each.customer.code
                                            move_dict['drug_specifications'] = str(
                                                i.product.template.drug_specifications)
                                            if i.to_location == self.location:
                                                moves_content.append(move_dict)
                                        else:
                                            pass
                                if moves_content == []:
                                    pass
                                else:
                                    moves_content[0]['number'] = str(each.number)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                                for i in moves_content:
                                    lists.append(i)

                    Return_product = return_product.search(return_drug)
                    for each in Return_product:
                        if each.warehouse == self.get_user_warehouse:
                            moves_content = []
                            move_line = each.moves
                            if self.product != None:
                                move_purchase_id = []
                                list_purchase_id = []
                                for i in move_line:
                                    dict_move = {}
                                    dict_move[i.product.id] = i.id
                                    move_purchase_id.append(dict_move)
                                    for move_each in move_purchase_id:
                                        if move_each.keys()[0] != product_id:
                                            pass
                                        else:
                                            list_purchase_id.append(move_each[product_id])
                                for i in list_purchase_id:
                                    message_move = Move.search([('id', '=', i)])
                                    if message_move:
                                        moves_purchase_content = []
                                        for i in message_move:
                                            if self.drug_type == None:
                                                move_dict = {}
                                                move_dict['product'] = i.product.name
                                                if i.list_price == None:
                                                    pass
                                                else:
                                                    move_dict['list_price'] = i.list_price
                                                if i.cost_price == None:
                                                    pass
                                                else:
                                                    move_dict['cost_price'] = i.cost_price
                                                move_dict['code'] = i.product.code
                                                move_dict['additional'] = i.product.template.attach
                                                try:
                                                    i.lot.number
                                                    move_dict['lot'] = str(i.lot.number)
                                                except:
                                                    pass
                                                try:
                                                    i.lot.shelf_life_expiration_date
                                                    move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                except:
                                                    pass
                                                move_dict['company'] = i.uom
                                                move_dict['effective_date'] = str(each.effective_date)
                                                move_dict['odd_numbers'] = str(i.real_number)
                                                move_dict['proposal'] = str(i.quantity)
                                                move_dict['drug_receiving_section'] = str(each.customer.name)
                                                move_dict['drug_receiving_code'] = str(each.customer.code)
                                                move_dict['drug_specifications'] = str(
                                                    i.product.template.drug_specifications)
                                                if i.from_location == self.location:
                                                    moves_purchase_content.append(move_dict)
                                            else:
                                                categories = [cate.id for cate in i.product.categories][0]
                                                uom_category = UomCategory.search([('id', '=', categories)])
                                                uom_name = uom_category[0].name
                                                if self.drug_type == uom_name:
                                                    move_dict = {}
                                                    move_dict['product'] = i.product.name
                                                    if i.list_price == None:
                                                        pass
                                                    else:
                                                        move_dict['list_price'] = i.list_price
                                                    if i.cost_price == None:
                                                        pass
                                                    else:
                                                        move_dict['cost_price'] = i.cost_price
                                                    move_dict['code'] = i.product.code
                                                    move_dict['additional'] = i.product.template.attach
                                                    try:
                                                        i.lot.number
                                                        move_dict['lot'] = str(i.lot.number)
                                                    except:
                                                        pass
                                                    try:
                                                        i.lot.shelf_life_expiration_date
                                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                                    except:
                                                        pass
                                                    move_dict['company'] = i.uom
                                                    move_dict['effective_date'] = str(each.effective_date)
                                                    move_dict['odd_numbers'] = str(i.real_number)
                                                    move_dict['proposal'] = str(i.quantity)
                                                    move_dict['drug_receiving_section'] = each.customer.name
                                                    move_dict['drug_receiving_code'] = each.customer.code
                                                    move_dict['drug_specifications'] = str(
                                                        i.product.template.drug_specifications)
                                                    if i.from_locatiom == self.location:
                                                        moves_purchase_content.append(move_dict)
                                                else:
                                                    pass
                                    if moves_purchase_content == []:
                                        pass
                                    else:
                                        moves_purchase_content[0]['number'] = str(each.number)
                                        moves_purchase_content[0]['processing_time'] = str(each.effective_date)
                                    for i in moves_purchase_content:
                                        lists.append(i)
                            else:
                                for i in move_line:
                                    if self.drug_type == None:
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_receiving_section'] = each.customer.name
                                        move_dict['drug_receiving_code'] = each.customer.code
                                        move_dict['drug_specifications'] = str(
                                            i.product.template.drug_specifications)
                                        if i.from_location == self.location:
                                            moves_content.append(move_dict)
                                        else:
                                            pass
                                    elif self.drug_type == '06':
                                        move_dict = {}
                                        move_dict['product'] = i.product.name
                                        if i.list_price == None:
                                            pass
                                        else:
                                            move_dict['list_price'] = i.list_price
                                        if i.cost_price == None:
                                            pass
                                        else:
                                            move_dict['cost_price'] = i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        move_dict['effective_date'] = str(each.effective_date)
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_receiving_section'] = each.customer.name
                                        move_dict['drug_receiving_code'] = each.customer.code
                                        move_dict['drug_specifications'] = str(
                                            i.product.template.drug_specifications)

                                        if i.from_location == self.location:
                                            moves_content.append(move_dict)
                                    else:
                                        categories = [cate.id for cate in i.product.categories][0]
                                        uom_category = UomCategory.search([('id', '=', categories)])
                                        uom_name = uom_category[0].name
                                        if self.drug_type == uom_name:
                                            move_dict = {}
                                            move_dict['product'] = i.product.name
                                            if i.list_price == None:
                                                pass
                                            else:
                                                move_dict['list_price'] = i.list_price
                                            if i.cost_price == None:
                                                pass
                                            else:
                                                move_dict['cost_price'] = i.cost_price
                                            move_dict['code'] = i.product.code
                                            move_dict['additional'] = i.product.template.attach
                                            try:
                                                i.lot.number
                                                move_dict['lot'] = str(i.lot.number)
                                            except:
                                                pass
                                            try:
                                                i.lot.shelf_life_expiration_date
                                                move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                            except:
                                                pass
                                            move_dict['company'] = i.uom
                                            move_dict['effective_date'] = str(each.effective_date)
                                            move_dict['odd_numbers'] = str(i.real_number)
                                            move_dict['proposal'] = str(i.quantity)
                                            move_dict['drug_receiving_section'] = each.customer.name
                                            move_dict['drug_receiving_code'] = each.customer.code
                                            move_dict['drug_specifications'] = str(
                                                i.product.template.drug_specifications)
                                            if i.from_location == self.location:
                                                moves_content.append(move_dict)
                                        else:
                                            pass
                                if moves_content == []:
                                    pass
                                else:
                                    moves_content[0]['number'] = str(each.number)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                                for i in moves_content:
                                    lists.append(i)
                    finnaly_list = sorted(lists, key=lambda x: (x['effective_date']), reverse=True)
                    self.move_query_department = finnaly_list
            if self.detailed_project == 'project_query':
                if self.start_time != None:
                    condition.append(('effective_date', '>=', self.start_time))
                    move_condition.append(('effective_date', '>=', self.start_time))
                if self.end_time != None:
                    condition.append(('effective_date', '<=', self.end_time))
                    move_condition.append(('effective_date', '<=', self.end_time))
                if self.number != u'':
                    condition.append(('number', '=', self.number))
                    move_condition.append(('number', '=', self.number))
                if self.document_type == '00':  # 请领单
                    condition.append(('starts', 'in', ['00', '06']))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '01':  # 请退单
                    condition.append(('starts', '=', '01'))
                    condition.append(('from_location', '=', self.location_frozen))
                if self.document_type == '02':  # 内部调拨出库
                    condition.append(('starts', '=', '04'))
                    condition.append(('from_location', '=', self.location))
                if self.document_type == '03':  # 内部调拨入库
                    condition.append(('starts', '=', '04'))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '04':  # 冻结转非限制
                    condition.append(('starts', '=', '03'))
                    condition.append(('from_location', '=', self.location_frozen))
                    condition.append(('to_location', '=', self.location))
                if self.document_type == '05':  # 非限制转冻结
                    condition.append(('starts', '=', '02'))
                    condition.append(('from_location', '=', self.location))
                    condition.append(('to_location', '=', self.location_frozen))
                if self.product != None:
                    Internal = internal.search(condition)
                    if Internal:
                        inter_lists = []
                        product_id = self.product.id
                        for each in Internal:
                            move_list_id = []
                            move_line = each.moves
                            for i in move_line:
                                move_list_id.append(i.product.id)
                            if product_id in move_list_id:
                                if self.drug_type == None:
                                    inter_lists.append(each.id)
                                elif self.drug_type == '06':
                                    inter_lists.append(each.id)
                                else:
                                    categories = [cate.id for cate in i.product.categories][0]
                                    uom_category = UomCategory.search([('id', '=', categories)])
                                    uom_name = uom_category[0].name
                                    if self.drug_type == uom_name:
                                        inter_lists.append(each.id)
                                    else:
                                        pass
                        lists_reult = []
                        for inter in inter_lists:
                            message_internal = internal.search([('id', '=', inter)])
                            if message_internal:
                                for message in message_internal:
                                    lv = {}
                                    lv['number'] = str(each.number)
                                    lv['processing_time'] = str(each.effective_date)
                                    lists_reult.append(lv)
                                    message_list = []
                                    list_move = []
                                    for i in message.moves:
                                        if self.product.id == i.product.id:
                                            message_dict = {}
                                            message_dict['product'] = i.product.name
                                            message_dict['list_price'] = i.list_price
                                            message_dict['cost_price'] = i.cost_price
                                            # message_dict['company'] = i.product.template.uom
                                            message_dict['lot'] = str(i.lot.number)
                                            message_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                            if i.real_number == None:
                                                message_dict['odd_numbers'] = ''
                                            else:
                                                if self.document_type == '01':
                                                    message_dict['odd_numbers'] = '-' + str(i.real_number)
                                                else:
                                                    message_dict['odd_numbers'] = str(i.real_number)
                                            if self.document_type == '01':
                                                message_dict['proposal'] = '-' + str(i.quantity)
                                            else:
                                                message_dict['proposal'] = str(i.quantity)
                                            message_dict['drug_specifications'] = str(
                                                i.product.template.drug_specifications)
                                            message_list.append(message_dict)
                                        else:
                                            pass
                                    if message_list == []:
                                        pass
                                    else:
                                        if self.document_type == '02':
                                            message_list[-1]['number'] = str(i.shipment.number)
                                        else:
                                            message_list[0]['number'] = str(i.shipment.number)
                                    message_lists = sorted(message_list, key=lambda x: (x['odd_numbers']), reverse=True)

                                    for i in message_lists:
                                        list_move.append(i)
                                    if self.document_type == '00':
                                        lv['move_query_apply'] = list_move
                                    if self.document_type == '01':
                                        lv['move_query_return'] = list_move
                                    if self.document_type == '02':
                                        lv['move_query_allocation'] = list_move
                                    if self.document_type == '03':
                                        lv['move_query_allocation'] = list_move
                                    if self.document_type == '04':
                                        lv['move_query_frozen'] = list_move
                                    if self.document_type == '05':
                                        lv['move_query_frozen'] = list_move
                        if self.document_type == '06':
                            self.move_project = []
                        if self.document_type == '07':
                            self.move_project = []
                        if self.document_type == '08':
                            self.move_project = []
                        else:
                            self.move_project = lists_reult

                else:
                    Internal = internal.search(condition)
                    if Internal:
                        lists = []
                        for each in Internal:
                            lv = {}
                            lv['number'] = str(each.number)
                            lv['processing_time'] = str(each.effective_date)

                            moves_content = []
                            move_line_list = []
                            move_line = each.moves
                            for i in move_line:
                                if self.drug_type == None:
                                    move_dict = {}
                                    move_dict['product'] = i.product.name
                                    move_dict['list_price'] = i.list_price
                                    move_dict['cost_price'] = i.cost_price
                                    move_dict['code'] = i.product.code
                                    move_dict['additional'] = i.product.template.attach
                                    try:
                                        i.lot.number
                                        move_dict['lot'] = str(i.lot.number)
                                    except:
                                        pass
                                    try:
                                        i.lot.shelf_life_expiration_date
                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                    except:
                                        pass
                                    move_dict['company'] = i.uom
                                    if i.real_number == None:
                                        move_dict['odd_numbers'] = ''
                                    else:
                                        if self.document_type == '01':
                                            move_dict['odd_numbers'] = '-' + str(i.real_number)
                                        else:
                                            move_dict['odd_numbers'] = str(i.real_number)
                                    if self.document_type == '01':
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                    else:
                                        move_dict['proposal'] = str(i.quantity)
                                    move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                    moves_content.append(move_dict)
                                elif self.drug_type == '06':
                                    move_dict = {}
                                    move_dict['product'] = i.product.name
                                    move_dict['code'] = i.product.code
                                    move_dict['additional'] = i.product.template.attach
                                    move_dict['list_price'] = i.list_price
                                    move_dict['cost_price'] = i.cost_price
                                    try:
                                        i.lot.number
                                        move_dict['lot'] = str(i.lot.number)
                                    except:
                                        pass
                                    try:
                                        i.lot.shelf_life_expiration_date
                                        move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                    except:
                                        pass
                                    move_dict['company'] = i.uom
                                    if self.document_type == '01':
                                        move_dict['odd_numbers'] = '-' + str(i.real_number)
                                        move_dict['proposal'] = '-' + str(i.quantity)
                                    else:
                                        move_dict['odd_numbers'] = str(i.real_number)
                                        move_dict['proposal'] = str(i.quantity)
                                    move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                    moves_content.append(move_dict)
                                else:
                                    move_dict = {}
                                    categories = [cate.id for cate in i.product.categories][0]
                                    uom_category = UomCategory.search([('id', '=', categories)])
                                    uom_name = uom_category[0].name
                                    if self.drug_type == uom_name:
                                        move_dict['product'] = i.product.name
                                        move_dict['list_price'] = i.list_price
                                        move_dict['cost_price'] = i.cost_price
                                        move_dict['code'] = i.product.code
                                        move_dict['additional'] = i.product.template.attach
                                        try:
                                            i.lot.number
                                            move_dict['lot'] = str(i.lot.number)
                                        except:
                                            pass
                                        try:
                                            i.lot.shelf_life_expiration_date
                                            move_dict['time'] = str(i.lot.shelf_life_expiration_date)
                                        except:
                                            pass
                                        move_dict['company'] = i.uom
                                        if i.real_number == None:
                                            move_dict['odd_numbers'] = ''
                                        else:
                                            if self.document_type == '01':
                                                move_dict['odd_numbers'] = '-' + str(i.real_number)
                                            else:
                                                move_dict['odd_numbers'] = str(i.real_number)
                                        if self.document_type == '01':
                                            move_dict['proposal'] = '-' + str(i.quantity)
                                        else:
                                            move_dict['proposal'] = str(i.quantity)
                                        move_dict['drug_specifications'] = str(i.product.template.drug_specifications)
                                        moves_content.append(move_dict)
                                    else:
                                        pass
                            if moves_content == []:
                                pass
                            else:
                                if self.document_type == '02':
                                    moves_content[-1]['number'] = str(each.number)
                                    moves_content[-1]['processing_time'] = str(each.effective_date)
                                else:
                                    moves_content[0]['number'] = str(each.number)
                                    moves_content[0]['processing_time'] = str(each.effective_date)
                            moves_contents = sorted(moves_content, key=lambda x: (x['odd_numbers']), reverse=True)
                            for i in moves_contents:
                                move_line_list.append(i)
                            if self.document_type == '00':
                                if move_line_list != []:
                                    lv['move_query_apply'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass
                            if self.document_type == '01':
                                if move_line_list != []:
                                    lv['move_query_return'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass
                            if self.document_type == '02':
                                if move_line_list != []:
                                    lv['move_query_allocation'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass
                            if self.document_type == '03':
                                if move_line_list != []:
                                    lv['move_query_allocation'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass

                            if self.document_type == '04':
                                if move_line_list != []:
                                    lv['move_query_frozen'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass
                            if self.document_type == '05':
                                if move_line_list != []:
                                    lv['move_query_frozen'] = move_line_list
                                    lists.append(lv)
                                else:
                                    pass
                        if self.document_type == '06':
                            lists = []
                            self.move_project = []
                        if self.document_type == '07':
                            lists = []
                            self.move_project = []
                        if self.document_type == '08':
                            lists = []
                            self.move_project = []
                        else:
                            self.move_project = lists
        else:
            self.move_project = []
            self.move_query_apply = []
            self.move_query_return = []
            self.move_query_allocation = []
            self.move_query_frozen = []
            self.move_query_scrap = []
            self.move_query_purchase = []
            self.move_query_department = []

    @staticmethod
    def default_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_id()

    @staticmethod
    def default_location_frozen():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_frozen_id()

    @staticmethod
    def default_get_user_warehouse():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_warehouse()

    @staticmethod
    def default_document_type():
        return '00'

    @staticmethod
    def default_detailed_query():
        return True

    @staticmethod
    def default_detailed_project():
        return 'detailed_query'

    @fields.depends('project_query', 'detailed_query')
    def on_change_project_query(self):
        if self.project_query == True:
            self.detailed_query = False
            self.message_find = False
        if self.project_query == False:
            self.detailed_query = True
            self.message_find = False

    @fields.depends('project_query', 'detailed_query')
    def on_change_detailed_query(self):
        if self.detailed_query == True:
            self.project_query = False
        if self.detailed_query == False:
            self.project_query = True


class InternalQueryWizard(Wizard):
    'Internal Query Wizard'

    __name__ = 'hrp_internal_delivery.internal_query_wizard'

    start = StateView('hrp_internal_delivery.internal_query',
                      'hrp_internal_delivery.internal_query_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Print', 'print_', 'tryton-print', default=True),
                      ])
    print_ = StateReport('hrp_internal_delivery.general_journal')

    def do_print_(self, action):
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        return action, data


class GeneralJournal(Report):
    __name__ = 'hrp_internal_delivery.general_journal'

    @classmethod
    def _get_records(cls, ids, model, data):
        Location = Pool().get('stock.location')
        location = Location.search([('id', '=', data['start']['location'])])[0].name
        data['start']['location_name'] = location
        return [data]

    @classmethod
    def get_context(cls, records, data):
        super(GeneralJournal, cls).get_context(records, {})
        report_context = super(GeneralJournal, cls).get_context(records, data)
        return report_context


class InternalDetailed(ModelView):
    """Internal Detailed"""

    __name__ = 'hrp_internal_delivery.internal_detailed'
    _rec_name = 'number'

    number = fields.Char('number')  # 单号
    processing_time = fields.Char('processing_time')  # 处理时间
    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品名称
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    time = fields.Char('time')  # 有效期
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格
    additional = fields.Char('additional')  # 附加


class InternalProject(ModelView):
    """Internal Project"""

    __name__ = 'hrp_internal_delivery.internal_project'
    _rec_name = 'number'

    number = fields.Char('number')  # 单号
    processing_time = fields.Char('processing_time')  # 处理时间
    # project_query = fields.Boolean('project_query',states={
    #     'invisible':True
    # })  #项目查询

    detailed_project = fields.Selection([
        ('detailed_query', u'明细查询'),
        ('project_query', u'项目查询')
    ], 'detailed_project', select=True, states={
        'invisible': True
    })  # 查询类别

    document_type = fields.Selection([
        ('00', u'请领单'),
        ('01', u'请退单'),
        ('02', u'调拨出库'),
        ('03', u'调拨入库'),
        ('04', u'冻结转非限制'),
        ('05', u'非限制转冻结'),
        ('06', u'报损单'),
        ('07', u'无采购订单'),
        ('08', u'科室领药单'),
    ], 'document_type', select=True, states={
        'invisible': True
    })  # 单据类型
    move_query_apply = fields.One2Many('hrp_internal_delivery.query_apply_done', 'None', 'move_query_apply', states={
        'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '00')
    }, depends=['project_query', 'document_type'])  # 请领

    move_query_return = fields.One2Many('hrp_internal_delivery.query_return_done', 'None', 'move_query_return', states={
        'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '01')
    }, depends=['project_query', 'document_type'])  # 请退

    move_query_allocation = fields.One2Many('hrp_internal_delivery.query_allocation_done', 'None',
                                            'move_query_allocation', states={
            'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '02') &
                                                                             ~Equal(
                                                                                 Eval('document_type'), '03')
        }, depends=['project_query', 'document_type'])  # 内部调拨

    move_query_frozen = fields.One2Many('hrp_internal_delivery.query_frozen_done', 'None', 'move_query_frozen'
                                        , states={
            'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '04') &
                                                                             ~Equal(Eval('document_type'), '05')
        }, depends=['project_query', 'document_type'])  # 不合格

    move_query_scrap = fields.One2Many('hrp_internal_delivery.query_scrap_done', 'None', 'move_query_scrap', states={
        'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '06')
    }, depends=['project_query', 'document_type'])  # 报废

    move_query_purchase = fields.One2Many('hrp_internal_delivery.query_purchase_done', 'None', 'move_query_purchase',
                                          states={
                                              'invisible': ~Equal(Eval('detailed_project'), 'project_query')
                                                           | ~Equal(Eval('document_type'), '07')
                                          }, depends=['project_query', 'document_type'])  # 无采购

    move_query_department = fields.One2Many('hrp_internal_delivery.query_department_done', 'None',
                                            'move_query_department', states={
            'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(Eval('document_type'), '08')
        }, depends=['project_query', 'document_type'])  # 科室领药单


class ContentInternalProject(ModelView):
    """Test Internal Project"""

    __name__ = 'hrp_internal_delivery.content_internal_project'
    _rec_name = 'number'

    product_name = fields.Char('product_name', select=True, readonly=True)  # 产品名称
    drug_specifications = fields.Char('drug_specifications', select=True, readonly=True)  # 规格
    company = fields.Char('company')  # 单位
    lot = fields.Char('lot')  # 批次
    time = fields.Char('time')  # 有效期
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格
    additional = fields.Char('additional')  # 附加


###############  请领单完成  ###############
class QueryApplyDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_apply_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    odd_numbers = fields.Char('odd_numbers')  # 请领数量
    proposal = fields.Char('proposal')  # 实发数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格


###############      请退单完成    ###############
class QueryReturnDone(ModelView):
    'Query Apply Done'
    __name__ = 'hrp_internal_delivery.query_return_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    odd_numbers = fields.Char('odd_numbers')  # 建议请领数量
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格


###############   内部调拨出货完成  ###############
class QueryAllocationDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_allocation_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    odd_numbers = fields.Char('odd_numbers')  # 建议请领数量
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格


###############   不合格管理()  ###############
class QueryFrozenDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_frozen_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    # odd_numbers = fields.Char('odd_numbers')  #建议请领数量
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格


###############   报损单  ###############

class QueryScrapDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_scrap_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    # odd_numbers = fields.Char('odd_numbers')  # 建议请领数量
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格
    state = fields.Selection([
        ('assigned', u'未审核'),
        ('cancel', u'取消'),
        ('done', u'已审核')], 'state', select=True)  # 单据状态
    why = fields.Selection([
        ('00', u'药品过期'),
        ('01', u'无外标签'),
        ('02', u'原包装破损'),
        ('03', u'科室自用'),
        ('04', u'近期药品'),
        ('05', u'长期不用'),
        ('06', u'停药'),
        ('07', u'病人退药'),
        ('08', u'工作失误'),
        ('09', u'单据错误'),
        ('10', u''),
    ], 'Why', depends=['caustic_why'])  # 报废原因
    create_user = fields.Char('create_user', select=True)  # 报单人
    write_user = fields.Char('write_user', select=True)  # 审核人
    write_time = fields.Char('write_time', select=True)  # 审核时间


###############   无采购单  ###############
class QueryPurchaseDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_purchase_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    effective_date = fields.Char('effective_date')  # 排序时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    # odd_numbers = fields.Char('odd_numbers')  # 建议请领数量
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格


###############   科室领药单  ###############
class QueryDepartmentDone(ModelView):
    """Query Apply Done"""
    __name__ = 'hrp_internal_delivery.query_department_done'

    number = fields.Char('number')  # 单号
    code = fields.Char('code', select=True)  # 编码
    processing_time = fields.Char('processing_time')  # 处理时间
    effective_date = fields.Char('effective_date')  # 排序时间
    product = fields.Char('product', select=True, readonly=True)  # 产品
    drug_specifications = fields.Char('drug_specifications')  # 规格
    company = fields.Many2One('product.uom', 'company')  # 单位
    lot = fields.Char('lot')  # 批次
    additional = fields.Char('additional')  # 附加
    time = fields.Char('time')  # 有效期至
    proposal = fields.Char('proposal')  # 请领数量
    cost_price = fields.Numeric('cost_price', digits=(16, 2))  # 批发价格
    list_price = fields.Numeric('list_price', digits=(16, 2))  # 零售价格
    drug_receiving_section = fields.Char('drug_receiving_section', select=True)  # 领药科室
    drug_receiving_code = fields.Char('drug_receiving_code', select=True)  # 科室编码
