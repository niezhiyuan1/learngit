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
from sql import Literal, Join
from sql.aggregate import Max

__all__ = ['HrpOutboundStatisticsReportOne', 'HrpOutboundStatisticsReportProduct', 'HrpOutboundStatisticsContent',
           'HrpOutboundStatisticsReportCustomer', 'HrpOutboundStatisticsWizard']


class HrpOutboundStatisticsReportOne(ModelSQL, ModelView):
    """Hrp Outbound Statistics Report One"""

    __name__ = "hrp_report.hrp_outbound_statistics_report_one"

    customer = fields.Function(fields.Many2One('party.party', 'customer'), 'get_customer')  # 领药科室
    number = fields.Char('number', select=True)  # 出库单号
    effective_date = fields.Function(fields.Date('effective_date', select=True), 'get_effective_date')  # 出库日期
    list_price = fields.Function(fields.Numeric('list_price', select=True), 'get_list_price')  # 零售金额
    cost_price = fields.Function(fields.Numeric('cost_price', select=True), 'get_cost_price')  # 批发金额

    @staticmethod
    def table_query(self=None):
        UomCategory = Pool().get('product.category')
        Number = Pool().get('order_no')
        number = Number.__table__()

        ConsumeProduct = Pool().get('stock.shipment.out.return')
        consume_product = ConsumeProduct.__table__()

        ReturnProduct = Pool().get('stock.shipment.out')
        return_product = ReturnProduct.__table__()

        where = Literal(True)
        join1 = Join(number, consume_product)
        join1.condition = join1.right.warehouse == number.location
        join2 = Join(join1, return_product)
        join2.condition = join2.right.warehouse == join1.right.warehouse

        content = [('order_category', 'in', ['sale_return', 'sale_purchase'])]
        if Transaction().context.get('start_time') != None:
            content.append(('time', '>=', Transaction().context.get('start_time')), )

        if Transaction().context.get('end_time') != None:
            content.append(('time', '<=', Transaction().context.get('end_time')), )

        if Transaction().context.get('drug_type') == '00':
            drug_type_name = u'西药'
        if Transaction().context.get('drug_type') == '01':
            drug_type_name = u'中成药'
        if Transaction().context.get('drug_type') == '02':
            drug_type_name = u'中草药'
        if Transaction().context.get('drug_type') == '03':
            drug_type_name = u'颗粒中'
        if Transaction().context.get('drug_type') == '04':
            drug_type_name = u'原料药'
        if Transaction().context.get('drug_type') == '05':
            drug_type_name = u'敷药'
        if Transaction().context.get('drug_type') == '07':
            drug_type_name = u'同位素'

        if Transaction().context.get('location'):
            content.append(('location', '=', Transaction().context.get('location')), )
            numbers_id = []
            start_id = []
            number_num = []
            number_end = []
            finally_id = []
            number_id = Number.search(content)
            for i in number_id:
                number_dict = {}
                number_dict['id'] = i.id
                number_dict['number'] = i.number
                numbers_id.append(number_dict)
                number_num.append(i.number)
                start_id.append(i.id)
            if Transaction().context.get('customer'):
                for each in number_num:
                    if Transaction().context.get('drug_type') == '06':
                        cosum_ = ConsumeProduct.search([('number', '=', each)])
                        if cosum_:
                            for cosum_each in cosum_:
                                if cosum_each.customer.id == Transaction().context.get('customer'):
                                    number_end.append(each)
                                else:
                                    pass
                        else:
                            pass

                        return_ = ReturnProduct.search([('number', '=', each)])
                        if return_:
                            for return_each in return_:
                                if return_each.customer.id == Transaction().context.get('customer'):
                                    number_end.append(each)
                                else:
                                    pass

                    else:
                        cosum_ = ConsumeProduct.search([('number', '=', each)])
                        if cosum_:
                            for cosum_each in cosum_:
                                if cosum_each.customer.id == Transaction().context.get('customer'):
                                    incoming_moves = cosum_each.incoming_moves
                                    if incoming_moves:
                                        drug_type_id = []
                                        for orderpoint in incoming_moves:
                                            categories = [i.id for i in orderpoint.product.categories]
                                            uom_category = UomCategory.search([('id', '=', categories[0])])
                                            uom_name = uom_category[0].name
                                            if drug_type_name == uom_name:
                                                drug_type_id.append(1)
                                            else:
                                                pass
                                        if len(drug_type_id) != 0:
                                            number_end.append(each)
                                else:
                                    pass
                        else:
                            pass

                        return_ = ReturnProduct.search([('number', '=', each)])
                        if return_:
                            for return_each in return_:
                                if return_each.customer.id == Transaction().context.get('customer'):
                                    outgoing_moves = return_each.outgoing_moves
                                    if outgoing_moves:
                                        drug_type_id = []
                                        for orderpoint in outgoing_moves:
                                            categories = [i.id for i in orderpoint.product.categories]
                                            uom_category = UomCategory.search([('id', '=', categories[0])])
                                            uom_name = uom_category[0].name
                                            if drug_type_name == uom_name:
                                                drug_type_id.append(1)
                                            else:
                                                pass
                                        if len(drug_type_id) != 0:
                                            number_end.append(each)
                        else:
                            pass
                for num in number_end:
                    for all in numbers_id:
                        if all['number'] == num:
                            finally_id.append(all['id'])
                        else:
                            pass
                if finally_id == []:
                    where = Literal(False)
                else:
                    where &= number.id.in_(finally_id)
            else:
                if start_id == []:
                    where = Literal(False)
                else:
                    where &= number.id.in_(start_id)

        where &= number.order_category.in_([
            'sale_return',
            'sale_purchase',
        ])

        Result = number.select(
            number.id.as_('id'),
            Max(number.create_uid).as_('create_uid'),
            Max(number.create_date).as_('create_date'),
            Max(number.write_uid).as_('write_uid'),
            Max(number.write_date).as_('write_date'),
            number.number,
            where=where,
            group_by=number.id)
        return Result

    #
    # def get_customer(self, name):
    #     return '1'

    def get_list_price(self, name):
        UomCategory = Pool().get('product.category')
        if Transaction().context.get('drug_type') == '00':
            drug_type_name = u'西药'
        if Transaction().context.get('drug_type') == '01':
            drug_type_name = u'中成药'
        if Transaction().context.get('drug_type') == '02':
            drug_type_name = u'中草药'
        if Transaction().context.get('drug_type') == '03':
            drug_type_name = u'颗粒中'
        if Transaction().context.get('drug_type') == '04':
            drug_type_name = u'原料药'
        if Transaction().context.get('drug_type') == '05':
            drug_type_name = u'敷药'
        if Transaction().context.get('drug_type') == '07':
            drug_type_name = u'同位素'
        Move = Pool().get('stock.move')
        ReturnProduct = Pool().get('stock.shipment.out')
        ConsumeProduct = Pool().get('stock.shipment.out.return')
        Number = Pool().get('order_no')
        number = Number(self.id).number
        list_id = []

        cosum_ = ConsumeProduct.search([('number', '=', number)])
        if cosum_:
            for i in cosum_:
                list_id.append(i.id)
        else:
            pass

        return_ = ReturnProduct.search([('number', '=', number)])
        if return_:
            for i in return_:
                list_id.append(i.id)
        else:
            pass
        if list_id == []:
            return 0
        else:
            list_price = 0
            for move_id in list_id:
                shipment_consume = 'stock.shipment.out,' + str(move_id)
                move_consume = Move.search([('shipment', '=', shipment_consume)])
                if move_consume:
                    for i in move_consume:
                        if Transaction().context.get('drug_type') == '06':
                            if i.list_price == None:
                                pass
                            else:
                                list_price += i.list_price
                        else:
                            categories = [orderpoint.id for orderpoint in i.product.categories]
                            uom_category = UomCategory.search([('id', '=', categories[0])])
                            uom_name = uom_category[0].name
                            if drug_type_name == uom_name:
                                if i.list_price == None:
                                    pass
                                else:
                                    list_price += i.list_price
                            else:
                                pass
                else:
                    pass
            for move_id in list_id:
                shipment_return = 'stock.shipment.out.return,' + str(move_id)
                return_product = Move.search([('shipment', '=', shipment_return)])
                if return_product:
                    for i in return_product:
                        if Transaction().context.get('drug_type') == '06':
                            if i.list_price == None:
                                pass
                            else:
                                list_price -= i.list_price
                        else:
                            categories = [orderpoint.id for orderpoint in i.product.categories]
                            uom_category = UomCategory.search([('id', '=', categories[0])])
                            uom_name = uom_category[0].name
                            if drug_type_name == uom_name:
                                if i.list_price == None:
                                    pass
                                else:
                                    list_price -= i.list_price
                            else:
                                pass
                else:
                    pass
            return list_price / 2

    def get_cost_price(self, name):
        UomCategory = Pool().get('product.category')
        if Transaction().context.get('drug_type') == '00':
            drug_type_name = u'西药'
        if Transaction().context.get('drug_type') == '01':
            drug_type_name = u'中成药'
        if Transaction().context.get('drug_type') == '02':
            drug_type_name = u'中草药'
        if Transaction().context.get('drug_type') == '03':
            drug_type_name = u'颗粒中'
        if Transaction().context.get('drug_type') == '04':
            drug_type_name = u'原料药'
        if Transaction().context.get('drug_type') == '05':
            drug_type_name = u'敷药'
        if Transaction().context.get('drug_type') == '07':
            drug_type_name = u'同位素'
        Move = Pool().get('stock.move')
        ReturnProduct = Pool().get('stock.shipment.out')
        ConsumeProduct = Pool().get('stock.shipment.out.return')
        Number = Pool().get('order_no')
        number = Number(self.id).number
        list_id = []
        cosum_ = ConsumeProduct.search([('number', '=', number)])
        if cosum_:
            for i in cosum_:
                list_id.append(i.id)
        else:
            pass

        return_ = ReturnProduct.search([('number', '=', number)])
        if return_:
            for i in return_:
                list_id.append(i.id)
        else:
            pass

        if list_id == []:
            return 0
        else:
            cost_price = 0
            for move_id in list_id:
                shipment_consume = 'stock.shipment.out,' + str(move_id)
                move_consume = Move.search([('shipment', '=', shipment_consume)])
                if move_consume:
                    for i in move_consume:
                        if Transaction().context.get('drug_type') == '06':
                            if i.cost_price == None:
                                pass
                            else:
                                cost_price += i.cost_price
                        else:
                            categories = [orderpoint.id for orderpoint in i.product.categories]
                            uom_category = UomCategory.search([('id', '=', categories[0])])
                            uom_name = uom_category[0].name
                            if drug_type_name == uom_name:
                                if i.cost_price == None:
                                    pass
                                else:
                                    cost_price += i.cost_price
                            else:
                                pass
                else:
                    pass
            for move_id in list_id:
                shipment_return = 'stock.shipment.out.return,' + str(move_id)
                return_product = Move.search([('shipment', '=', shipment_return)])
                if return_product:
                    for i in return_product:
                        if Transaction().context.get('drug_type') == '06':
                            if i.cost_price == None:
                                pass
                            else:
                                cost_price -= i.cost_price
                        else:
                            categories = [orderpoint.id for orderpoint in i.product.categories]
                            uom_category = UomCategory.search([('id', '=', categories[0])])
                            uom_name = uom_category[0].name
                            if drug_type_name == uom_name:
                                if i.cost_price == None:
                                    pass
                                else:
                                    cost_price -= i.cost_price
                            else:
                                pass
                else:
                    pass
            return cost_price / 2

    def get_effective_date(self, name):
        Number = Pool().get('order_no')
        time = Number(self.id).time
        return time

    def get_customer(self, name):
        if Transaction().context.get('customer'):
            return Transaction().context.get('customer')
        else:
            return


            # 'stock.shipment.out'发药
            # 'stock.shipment.out.return'退药


class HrpOutboundStatisticsReportProduct(ModelSQL, ModelView):
    """Hrp Outbound Statistics Report Product"""

    __name__ = "hrp_report.hrp_outbound_statistics_report_product"

    customer = fields.Function(fields.Many2One('party.party', 'customer'), 'get_customer')  # 领药科室
    customer_id = fields.Many2One('party.party', 'customer_id')  # 领药科室

    effective_date = fields.Function(fields.Date('effective_date', select=True), 'get_effective_date')  # 出库日期
    product = fields.Many2One('product.product', 'product', select=True)  # 产品名称
    code = fields.Function(fields.Char('code', select=True), 'get_code')  # 编码
    drug_specifications = fields.Function(fields.Char('drug_specifications', select=True),
                                          'get_drug_specifications')  # 规格

    list_price = fields.Function(fields.Numeric('list_price', select=True), 'get_list_price')  # 零售金额
    cost_price = fields.Function(fields.Numeric('cost_price', select=True), 'get_cost_price')  # 批发金额
    quantity = fields.Function(fields.Char('quantity'), 'get_quantity')  # 数量

    @classmethod
    def __setup__(cls):
        super(HrpOutboundStatisticsReportProduct, cls).__setup__()
        cls._order = [('customer_id', 'ASC'), ('id', 'ASC')]

    @staticmethod
    def table_query(self=None):
        UomCategory = Pool().get('product.category')
        move = Pool().get('stock.move')
        Move = move.__table__()

        ConsumeProduct = Pool().get('stock.shipment.out.return')
        ReturnProduct = Pool().get('stock.shipment.out')

        where = Literal(True)

        content = []

        if Transaction().context.get('start_time') != None:
            content.append(('effective_date', '>=', Transaction().context.get('start_time')), )

        if Transaction().context.get('end_time') != None:
            content.append(('effective_date', '<=', Transaction().context.get('end_time')), )

        if Transaction().context.get('drug_type') == '00':
            drug_type_name = u'西药'
        if Transaction().context.get('drug_type') == '01':
            drug_type_name = u'中成药'
        if Transaction().context.get('drug_type') == '02':
            drug_type_name = u'中草药'
        if Transaction().context.get('drug_type') == '03':
            drug_type_name = u'颗粒中'
        if Transaction().context.get('drug_type') == '04':
            drug_type_name = u'原料药'
        if Transaction().context.get('drug_type') == '05':
            drug_type_name = u'敷药'
        if Transaction().context.get('drug_type') == '06':
            drug_type_name = u''
        if Transaction().context.get('drug_type') == '07':
            drug_type_name = u'同位素'
        if Transaction().context.get('location'):
            stock_move_id = []
            content.append(('warehouse', '=', Transaction().context.get('location')))

            consume_product = ConsumeProduct.search(content)
            if consume_product:
                for consume_each in consume_product:
                    consume_move = consume_each.incoming_moves
                    for move_each in consume_move:
                        categories = [i.id for i in move_each.product.categories]
                        uom_category = UomCategory.search([('id', '=', categories[0])])
                        uom_name = uom_category[0].name
                        if drug_type_name == '':
                            stock_move_id.append(move_each.id)
                        else:
                            if uom_name == drug_type_name:
                                stock_move_id.append(move_each.id)
                            else:
                                pass
            else:
                pass

            return_product = ReturnProduct.search(content)
            if return_product:
                for return_each in return_product:
                    return_move = return_each.outgoing_moves
                    for move_each in return_move:
                        categories = [i.id for i in move_each.product.categories]
                        uom_category = UomCategory.search([('id', '=', categories[0])])
                        uom_name = uom_category[0].name
                        if drug_type_name == '':
                            stock_move_id.append(move_each.id)
                        else:
                            if uom_name == drug_type_name:
                                stock_move_id.append(move_each.id)
                            else:
                                pass
            else:
                pass
            if stock_move_id == []:
                where = Literal(False)
            else:
                if Transaction().context.get('customer'):
                    party_move_id = []
                    for move_party in stock_move_id:
                        move_party_id = move.search([('id', '=', move_party)])[0].party.id
                        if Transaction().context.get('customer') == move_party_id:
                            party_move_id.append(move_party)
                        else:
                            pass
                    where &= Move.id.in_(party_move_id)
                else:
                    where &= Move.id.in_(stock_move_id)
                party_list = []
                for each_move in stock_move_id:
                    party_dict = {}
                    move_number = move.search([('id', '=', each_move)])[0].shipment
                    return_consume = str(move_number).split(',')
                    return_consume_id = int(return_consume[-1])
                    return_or_consume = return_consume[0]
                    if return_or_consume == 'stock.shipment.out.return':
                        consume_party = ConsumeProduct.search([('id', '=', return_consume_id)])[0].customer.name
                        consume_party_id = ConsumeProduct.search([('id', '=', return_consume_id)])[0].customer.id
                        party_dict['party'] = consume_party
                        party_dict['party_id'] = consume_party_id
                        party_dict['move_id'] = each_move
                        party_list.append(party_dict)
                    if return_or_consume == 'stock.shipment.out':
                        return_party = ReturnProduct.search([('id', '=', return_consume_id)])[0].customer.name
                        return_party_id = ReturnProduct.search([('id', '=', return_consume_id)])[0].customer.id
                        party_dict['party'] = return_party
                        party_dict['party_id'] = return_party_id
                        party_dict['move_id'] = each_move
                        party_list.append(party_dict)
                    else:
                        pass
                sort_party_list = sorted(party_list, key=lambda x: (x['party'], x['move_id']), reverse=False)
                Transaction().set_context(find_list=sort_party_list)
        Result = Move.select(
            Move.id.as_('id'),
            Max(Move.create_uid).as_('create_uid'),
            Max(Move.create_date).as_('create_date'),
            Max(Move.write_uid).as_('write_uid'),
            Max(Move.write_date).as_('write_date'),
            Move.party.as_('customer_id'),
            Move.product,
            where=where,
            group_by=Move.id)
        return Result

    def get_effective_date(self, name):
        Date = Pool().get('ir.date')
        today = Date.today()
        return today

    def get_customer(self, name):
        customer = Transaction().context.get('find_list')
        if customer:
            list_dict = []
            for i in customer:
                list_dict.append(i['party_id'])
            list_party = list(set(list_dict))
            dicts = {}
            for each_list in list_party:
                num = 0
                for each in customer:
                    if each['party_id'] == each_list:
                        if num == 0:
                            num += 1
                            dicts[each['move_id']] = each['party_id']
                        else:
                            dicts[each['move_id']] = None
                    else:
                        pass
            return dicts[self.id]
        else:
            return None

    def get_list_price(self, name):
        move = Pool().get('stock.move')
        Move = move(self.id)
        consume_return = str(Move.shipment).split(',')[0]
        list_price = Move.list_price
        if consume_return == 'stock.shipment.out':
            return list_price
        else:
            return -list_price

    def get_cost_price(self, name):
        move = Pool().get('stock.move')
        Move = move(self.id)
        cost_price = Move.cost_price
        consume_return = str(Move.shipment).split(',')[0]
        if consume_return == 'stock.shipment.out':
            return cost_price
        else:
            return -cost_price

    def get_quantity(self, name):
        move = Pool().get('stock.move')
        Move = move(self.id)
        quantity = Move.quantity
        return quantity

    def get_code(self, name):
        move = Pool().get('stock.move')
        Move = move(self.id)
        code = Move.product.code
        return code

    def get_drug_specifications(self, name):
        move = Pool().get('stock.move')
        Move = move(self.id)
        drug_specifications = Move.product.drug_specifications
        return drug_specifications


class HrpOutboundStatisticsContent(ModelView):
    """Hrp Outbound Statistics Content"""

    __name__ = 'hrp_report.hrp_outbound_statistics_content'

    statistical_type = fields.Selection([
        ('01', u'单据汇总'),
        ('02', u'药品汇总'),
        ('03', u'科室汇总'),
    ], 'statistical_type', select=True, sort=False, required=True)  # 统计类型

    drug_type = fields.Selection([
        ('06', u'全部'),
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('07', u'同位素'),
    ], 'drug_type', select=True, sort=False, required=True)  # 药品类型
    location = fields.Many2One('stock.location', 'location')  # 所在部门
    customer = fields.Many2One('party.party', 'customer')  # 领／退药科室
    start_time = fields.Date('start_time', select=True)  # 开始时间
    end_time = fields.Date('end_time', select=True)  # 结束时间

    @staticmethod
    def default_drug_type():
        return '06'

    @staticmethod
    def default_location():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_warehouse()


class HrpOutboundStatisticsWizard(Wizard):
    """Hrp Outbound Statistics Wizard"""

    __name__ = 'hrp_report.hrp_outbound_statistics_wizard'

    start = StateView('hrp_report.hrp_outbound_statistics_content',
                      'hrp_report.hrp_outbound_statistics_content_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok', default=True),
                      ])
    create_ = StateTransition()
    report = StateAction('hrp_report.act_hrp_outbound_statistics_one')
    report_product = StateAction('hrp_report.act_hrp_outbound_statistics_product')
    report_customer = StateAction('hrp_report.act_hrp_hrp_outbound_statistics_customer')

    def transition_create_(self):
        if self.start.statistical_type == '02':
            return 'report_product'
        elif self.start.statistical_type == '01':
            return 'report'
        else:
            return 'report_customer'

    def do_report(self, action):
        dict = {}
        try:
            self.start.location.id
            dict['location'] = self.start.location.id
        except:
            pass
        try:
            self.start.drug_type
            dict['drug_type'] = self.start.drug_type
        except:
            pass
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
            self.start.customer.id
            dict['customer'] = self.start.customer.id
        except:
            pass
        try:
            action['pyson_context'] = PYSONEncoder().encode(dict)
        except:
            pass
        action['name'] += ' - (%s) @ %s' % (u'药库出库报表', self.start.start_time)
        return action, {}

    def do_report_product(self, action):
        dict = {}
        try:
            self.start.location.id
            dict['location'] = self.start.location.id
        except:
            pass
        try:
            self.start.drug_type
            dict['drug_type'] = self.start.drug_type
        except:
            pass
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
            self.start.customer.id
            dict['customer'] = self.start.customer.id
        except:
            pass
        try:
            action['pyson_context'] = PYSONEncoder().encode(dict)
        except:
            pass
        action['name'] += ' - (%s) @ %s' % (u'药库出库报表', str(self.start.start_time) + '——' + str(self.start.end_time))
        return action, {}


    def do_report_customer(self, action):
        dict = {}
        try:
            self.start.location.id
            dict['location'] = self.start.location.id
        except:
            pass
        try:
            self.start.drug_type
            dict['drug_type'] = self.start.drug_type
        except:
            pass
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
            self.start.customer.id
            dict['customer'] = self.start.customer.id
        except:
            pass
        try:
            action['pyson_context'] = PYSONEncoder().encode(dict)
        except:
            pass
        action['name'] += ' - (%s) @ %s' % (u'药库出库报表', str(self.start.start_time) + '——' + str(self.start.end_time))
        return action, {}


class HrpOutboundStatisticsReportCustomer(ModelSQL, ModelView):
    """Hrp Outbound Statistics Report Customer"""

    __name__ = "hrp_report.hrp_outbound_statistics_customer"

    customer = fields.Many2One('party.party', 'customer')  # 领药科室
    list_price = fields.Function(fields.Numeric('lost_price'), 'get_list_price')  # 零售金额
    cost_price = fields.Function(fields.Numeric('cost_price'), 'get_cost_price')  # 批发金额

    @staticmethod
    def table_query(self=None):
        UomCategory = Pool().get('product.category')
        move = Pool().get('stock.move')
        Move = move.__table__()

        ConsumeProduct = Pool().get('stock.shipment.out.return')
        ReturnProduct = Pool().get('stock.shipment.out')

        where = Literal(True)

        content = []

        if Transaction().context.get('start_time') != None:
            content.append(('effective_date', '>=', Transaction().context.get('start_time')), )

        if Transaction().context.get('end_time') != None:
            content.append(('effective_date', '<=', Transaction().context.get('end_time')), )

        if Transaction().context.get('drug_type') == '00':
            drug_type_name = u'西药'
        if Transaction().context.get('drug_type') == '01':
            drug_type_name = u'中成药'
        if Transaction().context.get('drug_type') == '02':
            drug_type_name = u'中草药'
        if Transaction().context.get('drug_type') == '03':
            drug_type_name = u'颗粒中'
        if Transaction().context.get('drug_type') == '04':
            drug_type_name = u'原料药'
        if Transaction().context.get('drug_type') == '05':
            drug_type_name = u'敷药'
        if Transaction().context.get('drug_type') == '06':
            drug_type_name = u''
        if Transaction().context.get('drug_type') == '07':
            drug_type_name = u'同位素'
        if Transaction().context.get('location'):
            stock_move_id = []
            content.append(('warehouse', '=', Transaction().context.get('location')))

            consume_product = ConsumeProduct.search(content)
            if consume_product:
                for consume_each in consume_product:
                    consume_move = consume_each.incoming_moves
                    for move_each in consume_move:
                        categories = [i.id for i in move_each.product.categories]
                        uom_category = UomCategory.search([('id', '=', categories[0])])
                        uom_name = uom_category[0].name
                        if drug_type_name == '':
                            stock_move_id.append(move_each.id)
                        else:
                            if uom_name == drug_type_name:
                                stock_move_id.append(move_each.id)
                            else:
                                pass
            else:
                pass

            return_product = ReturnProduct.search(content)
            if return_product:
                for return_each in return_product:
                    return_move = return_each.outgoing_moves
                    for move_each in return_move:
                        categories = [i.id for i in move_each.product.categories]
                        uom_category = UomCategory.search([('id', '=', categories[0])])
                        uom_name = uom_category[0].name
                        if drug_type_name == '':
                            stock_move_id.append(move_each.id)
                        else:
                            if uom_name == drug_type_name:
                                stock_move_id.append(move_each.id)
                            else:
                                pass
            else:
                pass
            if stock_move_id == []:
                where = Literal(False)
            else:

                party_list = []
                for each_move in stock_move_id:
                    party_dict = {}
                    move_number = move.search([('id', '=', each_move)])[0].shipment
                    return_consume = str(move_number).split(',')
                    return_consume_id = int(return_consume[-1])
                    return_or_consume = return_consume[0]
                    if return_or_consume == 'stock.shipment.out.return':
                        consume_party = ConsumeProduct.search([('id', '=', return_consume_id)])[0].customer.name
                        consume_party_id = ConsumeProduct.search([('id', '=', return_consume_id)])[0].customer.id
                        party_dict['party'] = consume_party
                        party_dict['party_id'] = consume_party_id
                        party_dict['move_id'] = each_move
                        party_list.append(party_dict)
                    if return_or_consume == 'stock.shipment.out':
                        return_party = ReturnProduct.search([('id', '=', return_consume_id)])[0].customer.name
                        return_party_id = ReturnProduct.search([('id', '=', return_consume_id)])[0].customer.id
                        party_dict['party'] = return_party
                        party_dict['party_id'] = return_party_id
                        party_dict['move_id'] = each_move
                        party_list.append(party_dict)
                    else:
                        pass
                party_id = []
                for i in party_list:
                    party_id.append(i['party_id'])
                set_party_id = list(set(party_id))
                party_dicts = {}
                for each in set_party_id:
                    move_list = []
                    for party in party_list:
                        if party['party_id'] == each:
                            move_list.append(party['move_id'])
                        else:
                            pass
                    party_dicts[each] = move_list
                party_value = party_dicts.values()

                Transaction().set_context(price=party_dicts)

                find_move_id = []
                for value in party_value:
                    find_move_id.append(value[0])
                if find_move_id == []:
                    where = Literal(False)
                else:
                    where &= Move.id.in_(find_move_id)

        Result = Move.select(
            Move.id.as_('id'),
            Max(Move.create_uid).as_('create_uid'),
            Max(Move.create_date).as_('create_date'),
            Max(Move.write_uid).as_('write_uid'),
            Max(Move.write_date).as_('write_date'),
            Move.party.as_('customer'),
            where=where,
            group_by=Move.id)
        return Result

    def get_list_price(self, name):
        move = Pool().get('stock.move')
        party_id = move(self.id).party.id
        price = Transaction().context.get('price')
        list_price = 0
        if price != {}:
            move_id = price[party_id]
            for i in move_id:
                list_price += move(i).list_price
        else:
            pass
        return list_price

    def get_cost_price(self, name):
        move = Pool().get('stock.move')
        party_id = move(self.id).party.id
        price = Transaction().context.get('price')
        cost_price = 0
        if price != {}:
            move_id = price[party_id]
            for i in move_id:
                cost_price += move(i).cost_price
        else:
            pass
        return cost_price
