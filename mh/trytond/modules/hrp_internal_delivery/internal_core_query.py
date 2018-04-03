# coding:utf-8
import time
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Equal, Bool
from trytond.report import Report
from trytond.wizard import StateReport
from trytond.wizard import Wizard, StateView, Button

__all__ = ['InternalCoreQuery', 'InternalCoreQueryWizard', 'InternalCoreDetailed', 'InternalCoreProject',
           'ContentInternalCoreProject',
           'QueryCoreFrozenDone', 'QueryCoreReturnDone', 'QueryCoreApplyDone', 'GeneralCoreJournal']


class InternalCoreQuery(ModelView):
    """Internal Core Query"""

    __name__ = 'hrp_internal_delivery.internal_core_query'
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
            Eval('move_query_frozen')) | Bool(Eval('move_query_purchase')) | Bool(Eval('move_query_department')) | Bool(
            Eval('move_project'))
    })  # 明细查询
    project_query = fields.Boolean('project_query', states={
        'readonly': Bool(Eval('move_query_apply')) | Bool(Eval('move_query_return')) | Bool(
            Eval('move_query_frozen')) | Bool(Eval('move_query_purchase')) | Bool(Eval('move_query_department')) | Bool(
            Eval('move_project'))
    })  # 项目查询
    document_type = fields.Selection([
        ('00', u'请领单'),
        ('01', u'请退单'),
        ('04', u'冻结转非限制'),
        ('05', u'非限制转冻结'),
    ], 'document_type', select=True, sort=False)  # 单据类型

    message_find = fields.Boolean('message_find')  # 查找

    move_detailed = fields.One2Many('hrp_internal_delivery.internal_core_detailed', 'None', 'move_detailed', states={
        'invisible': ~Bool(Eval('detailed_query'))
    })  # 明细表

    move_project = fields.One2Many('hrp_internal_delivery.internal_core_project', 'None', 'move_project', states={
        'invisible': ~Equal(Eval('detailed_project'), 'project_query')
    }, domain=[
        ('document_type', '=', Eval('document_type')),
        ('detailed_project', '=', Eval('detailed_project')),
    ], depends=['detailed_project', 'document_type'])  # 项目表

    move_query_apply = fields.One2Many('hrp_internal_delivery.query_core_apply_done', 'None', 'move_query_apply',
                                       states={
                                           'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(
                                               Eval('document_type'), '00')
                                       }, depends=['detailed_project', 'document_type'])  # 请领

    move_query_return = fields.One2Many('hrp_internal_delivery.query_core_return_done', 'None', 'move_query_return',
                                        states={
                                            'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(
                                                Eval('document_type'), '01')
                                        }, depends=['detailed_project', 'document_type'])  # 请退

    move_query_frozen = fields.One2Many('hrp_internal_delivery.query_core_frozen_done', 'None', 'move_query_frozen',
                                        states={
                                            'invisible': ~Equal(Eval('detailed_project'), 'detailed_query') | ~Equal(
                                                Eval('document_type'), '04') & ~Equal(Eval('document_type'), '05')
                                        }, depends=['detailed_project', 'document_type'])  # 不合格

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
                    'move_query_frozen', 'move_query_purchase', 'move_query_department')
    def on_change_message_find(self):
        UomCategory = Pool().get('product.category')
        internal = Pool().get('stock.shipment.internal')
        Move = Pool().get('stock.move')
        condition = []
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
                    return_drug.append(('effective_date', '>=', self.start_time))
                if self.end_time != None:
                    condition.append(('effective_date', '<=', self.end_time))
                    move_condition.append(('effective_date', '<=', self.end_time))
                    return_drug.append(('effective_date', '<=', self.end_time))
                if self.number != u'':
                    condition.append(('number', '=', self.number))
                    move_condition.append(('number', '=', self.number))
                    return_drug.append(('number', '=', self.number))
                if self.document_type == '00':  # 请领单
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', 'in', ['00', '06']))
                    condition.append(('from_location', '=', self.location))
                if self.document_type == '01':  # 请退单
                    condition.append(('state', '=', 'done'))
                    condition.append(('starts', '=', '01'))
                    condition.append(('to_location', '=', self.location_frozen))

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
                                    if i.quantity == 0:
                                        move_dict['cost_price'] = 0
                                        move_dict['list_price'] = 0
                                    else:
                                        if self.document_type == '01':
                                            move_dict['cost_price'] = -i.cost_price
                                            move_dict['list_price'] = -i.list_price
                                        else:
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
                                    if i.quantity == 0:
                                        move_dict['cost_price'] = 0
                                        move_dict['list_price'] = 0
                                    else:
                                        if self.document_type == '01':
                                            move_dict['cost_price'] = -i.cost_price
                                            move_dict['list_price'] = -i.list_price
                                        else:
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
                                        if i.quantity == 0:
                                            move_dict['cost_price'] = 0
                                            move_dict['list_price'] = 0
                                        else:
                                            if self.document_type == '01':
                                                move_dict['cost_price'] = -i.cost_price
                                                move_dict['list_price'] = -i.list_price
                                            else:
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
                            moves_contents = sorted(moves_content, key=lambda x: (x['code'], x['odd_numbers']),
                                                    reverse=True)
                            if moves_contents == []:
                                pass
                            else:
                                if self.document_type == '00':
                                    moves_contents[0]['number'] = str(each.number)
                                    moves_contents[0]['processing_time'] = str(each.effective_date)
                                else:
                                    moves_contents[-1]['number'] = str(each.number)
                                    moves_contents[-1]['processing_time'] = str(each.effective_date)

                            for i in moves_contents:
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
                    condition.append(('from_location', '=', self.location))
                if self.document_type == '01':  # 请退单
                    condition.append(('starts', '=', '01'))
                    condition.append(('to_location', '=', self.location_frozen))
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
                                    if i.quantity == 0:
                                        move_dict['list_price'] = 0
                                        move_dict['cost_price'] = 0
                                    else:
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
                                    if i.quantity == 0:
                                        move_dict['list_price'] = 0
                                        move_dict['cost_price'] = 0
                                    else:
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
                                        if i.quantity == 0:
                                            move_dict['list_price'] = 0
                                            move_dict['cost_price'] = 0
                                        else:
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
                        else:
                            self.move_project = lists

        else:
            self.move_project = []
            self.move_query_apply = []
            self.move_query_return = []
            self.move_query_allocation = []
            self.move_query_frozen = []
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


class InternalCoreQueryWizard(Wizard):
    'Internal Core Query Wizard'

    __name__ = 'hrp_internal_delivery.internal_core_query_wizard'

    start = StateView('hrp_internal_delivery.internal_core_query',
                      'hrp_internal_delivery.internal_core_query_view_form', [
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


class GeneralCoreJournal(Report):
    __name__ = 'hrp_internal_delivery.general_core_journal'

    @classmethod
    def _get_records(cls, ids, model, data):
        Location = Pool().get('stock.location')
        location = Location.search([('id', '=', data['start']['location'])])[0].name
        data['start']['location_name'] = location
        return [data]

    @classmethod
    def get_context(cls, records, data):
        super(GeneralCoreJournal, cls).get_context(records, {})
        report_context = super(GeneralCoreJournal, cls).get_context(records, data)
        return report_context


class InternalCoreDetailed(ModelView):
    'Internal Core Detailed'

    __name__ = 'hrp_internal_delivery.internal_core_detailed'
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


class InternalCoreProject(ModelView):
    'Internal Core Project'

    __name__ = 'hrp_internal_delivery.internal_core_project'
    _rec_name = 'number'

    number = fields.Char('number')  # 单号
    processing_time = fields.Char('processing_time')  # 处理时间

    detailed_project = fields.Selection([
        ('detailed_query', u'明细查询'),
        ('project_query', u'项目查询')
    ], 'detailed_project', select=True, states={
        'invisible': True
    })  # 查询类别

    document_type = fields.Selection([
        ('00', u'请领单'),
        ('01', u'请退单'),
        ('04', u'冻结转非限制'),
        ('05', u'非限制转冻结'),
    ], 'document_type', select=True, states={
        'invisible': True
    })  # 单据类型
    move_query_apply = fields.One2Many('hrp_internal_delivery.query_core_apply_done', 'None', 'move_query_apply',
                                       states={
                                           'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(
                                               Eval('document_type'), '00')
                                       }, depends=['project_query', 'document_type'])  # 请领

    move_query_return = fields.One2Many('hrp_internal_delivery.query_core_return_done', 'None', 'move_query_return',
                                        states={
                                            'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(
                                                Eval('document_type'), '01')
                                        }, depends=['project_query', 'document_type'])  # 请退

    move_query_frozen = fields.One2Many('hrp_internal_delivery.query_core_frozen_done', 'None', 'move_query_frozen',
                                        states={
                                            'invisible': ~Equal(Eval('detailed_project'), 'project_query') | ~Equal(
                                                Eval('document_type'), '04') & ~Equal(Eval('document_type'),
                                                                                      '05')
                                        }, depends=['project_query', 'document_type'])  # 不合格


class ContentInternalCoreProject(ModelView):
    'Test Internal  Core Project'

    __name__ = 'hrp_internal_delivery.content_internal_core_project'
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
class QueryCoreApplyDone(ModelView):
    'Query Apply Done'
    __name__ = 'hrp_internal_delivery.query_core_apply_done'

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
class QueryCoreReturnDone(ModelView):
    'Query Apply Done'
    __name__ = 'hrp_internal_delivery.query_core_return_done'

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
class QueryCoreFrozenDone(ModelView):
    'Query Core Apply Done'
    __name__ = 'hrp_internal_delivery.query_core_frozen_done'

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
