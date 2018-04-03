#coding:utf-8
import operator
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView,Button, StateAction


__all__ = ['InternalReturnRequest','InternalReturnRequestWizard','TestlReturnRequest']


class TestlReturnRequest(ModelView):
    'Internal Return Request'

    __name__ = 'hrp_new_product.test_return_request'
    _rec_name = 'number'


    product_name = fields.Char('product_name',select=True,readonly=True)#产品名字
    product = fields.Many2One("product.product", "Product", required=True,readonly=True)#产品
    from_location = fields.Many2One("stock.location","from_location",select=True,readonly=True)#
    to_location = fields.Many2One("stock.location","to_location",select=True,readonly=True)#
    code = fields.Char('code',select=True,readonly=True)#编码
    drug_specifications = fields.Char('drug_specifications',select=True,readonly=True)#规格
    uom = fields.Many2One('product.uom','company',select=True,readonly=True)#单位
    return_quantity = fields.Integer('Return Quantity',select=True,readonly=True)#请退数量
    comment = fields.Text('Comment',select=True)#备注
    can_return_quantity = fields.Float('Can Return Quantity',select=True,states={
       'readonly':Equal(Eval('examine'),'02'),
    })#可以退的药品数量
    examine = fields.Selection([
        ('00',u''),
        ('01',u'未审核'),
        ('02',u'已审核'),
    ],'Examine',select=True) #退药审核
    is_direct_sending = fields.Boolean('Is_direct_sending',select=True,readonly=True)#是否直送
    party = fields.Many2One('party.party','party',select=True)#供应商


    @classmethod
    def search_product(cls, name, domain=None):
        location_ids = Transaction().context.get('product')
        return cls._search_quantity(name, location_ids, domain,
            grouping=('product', 'product'))

class InternalReturnRequest(ModelView):
    'Internal Return Request'
    __name__ = 'hrp_new_product.internal_return_request'
    _rec_name = 'number'

    number = fields.Many2One('product.product','Number', select=True)
    starts = fields.Selection([
        ('00',u'西药'),
        ('01',u'中成药'),
        ('02',u'中草药'),
        ('03',u'颗粒中'),
        ('04',u'原料药'),
        ('05',u'敷药'),
        ('06',u' '),
        ('07',u'同位素')
    ],'Starts',select=True)
    # special = fields.Selection([
    #     ('00',u'直送'),
    #     ('01',u'精一'),
    #     ('02',u'麻醉'),
    # ],'special',select=True)
    # effective_date = fields.Date('Effective Date',
    #     states={
    #         'readonly': Eval('state').in_(['cancel', 'done']),
    #         },
    #     depends=['state'])
    # planned_date = fields.Date('Planned Date',readonly=True)

    company = fields.Many2One('company.company', 'Company', required=True)
    moves = fields.One2Many('hrp_new_product.test_return_request', '', 'Moves')


    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_moves():
        Date_ = Pool().get('ir.date')
        Product = Pool().get('product.product')
        MOVE = Pool().get('hrp_new_product.new_return')
        list = []
        return_drug = MOVE.search([])
        for i in return_drug:
            dict = {}
            dict['product'] = i.product.id
            dict['product_name'] = i.product.name
            product_templates = Pool().get('product.template')
            product_template = product_templates.search([
                ("id","=",i.product.template.id)
            ])
            if product_template == []:
                pass
            else:
                party = product_template[0].product_suppliers
                if party:
                    party = party[0].party.id
                    dict['party'] = party
                else:
                    pass
            dict['from_location'] = i.from_location.id
            dict['to_location'] = i.to_location.id
            dict['code'] = i.code
            dict['drug_specifications'] = i.drug_specifications
            with Transaction().set_context(stock_date_end=Date_.today()):
                quantities = Product.products_by_location([i.to_location.id],[i.product.id], with_childs=True)
            if quantities.values():
                return_quantity = [v for v in quantities.values()][0]
            else:
                return_quantity = 0
            if return_quantity <= 0:
                pass
            else:
                dict['return_quantity'] = return_quantity
                dict['uom'] = i.uom.id
                dict['examine'] = i.examine
                dict['can_return_quantity'] = i.can_return_quantity
                dict['is_direct_sending'] = i.is_direct_sending
                list.append(dict)
        list.sort()
        return list

    @fields.depends('number','moves')
    def on_change_number(self):
        if self.number == None:
            pass
        else:
            Product = Pool().get('product.product')
            MOVE = Pool().get('hrp_new_product.new_return')
            Name = self.number.template.name
            Date_ = Pool().get('ir.date')
            list=[]
            mmm = MOVE.search([
                ('product','=',Name)
            ])
            for i in mmm:
                dict = {}
                dict['product'] = i.product.id
                dict['from_location'] = i.from_location.id
                product_templates = Pool().get('product.template')
                product_template = product_templates.search([
                    ("id","=",i.product.id)
                ])
                if product_template:
                    party = product_template[0].product_suppliers
                    party = party[0].party.id
                    dict['party'] = party
                dict['to_location'] = i.to_location.id
                dict['code'] = i.code
                dict['drug_specifications'] = i.drug_specifications
                with Transaction().set_context(stock_date_end=Date_.today()):
                    quantities = Product.products_by_location([i.to_location.id],[i.product.id], with_childs=True)
                if quantities.values():
                    return_quantity = [v for v in quantities.values()][0]
                    if return_quantity <= 0:
                        continue
                dict['return_quantity'] = return_quantity
                dict['uom'] = i.uom.id
                dict['examine'] = i.examine
                dict['can_return_quantity'] = i.can_return_quantity
                dict['is_direct_sending'] = i.is_direct_sending
                list.append(dict)
            list.sort()
            self.moves = list

    @fields.depends('starts','moves')
    def on_change_starts(self):
        Date_ = Pool().get('ir.date')
        Product = Pool().get('product.product')
        MOVE = Pool().get('hrp_new_product.new_return')
        list = []
        scrap = []
        if self.starts == '06':
            pass
        else:
            scrap.append(('drug_type','=',self.starts))
        mmm = MOVE.search(scrap)
        for i in mmm:
            dict = {}
            dict['product'] = i.product.id
            dict['product_name'] = i.product.name
            product_templates = Pool().get('product.template')
            product_template = product_templates.search([
                ("id","=",i.product.template.id)
            ])
            if product_template:
                Party = product_template[0].product_suppliers
                party = Party[0].party.id
                dict['party'] = party
            else:
                pass
            dict['from_location'] = i.from_location.id
            dict['to_location'] = i.to_location.id
            dict['code'] = i.code
            dict['drug_specifications'] = i.drug_specifications
            with Transaction().set_context(stock_date_end=Date_.today()):
                    quantities = Product.products_by_location([i.to_location.id],[i.product.id], with_childs=True)
            if quantities.values():
                return_quantity = [v for v in quantities.values()][0]
                if return_quantity <= 0:
                    pass
                else:
                    dict['return_quantity'] = return_quantity
                    dict['uom'] = i.uom.id
                    dict['examine'] = i.examine
                    dict['can_return_quantity'] = i.can_return_quantity
                    dict['is_direct_sending'] = i.is_direct_sending
                    list.append(dict)
        list.sort()
        self.moves = list

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
        return super(InternalReturnRequest, cls).create(vlist)

    @classmethod
    def delete(cls, shipments):
        Move = Pool().get('stock.move')
        # Cancel before delete
        cls.cancel(shipments)
        for shipment in shipments:
            if shipment.state != 'cancel':
                cls.raise_user_error('delete_cancel', shipment.rec_name)
        Move.delete([m for s in shipments for m in s.moves])
        super(InternalReturnRequest, cls).delete(shipments)



class InternalReturnRequestWizard(Wizard):
    __name__ = 'hrp_new_product.internal_return_request_wizard'

    start = StateView('hrp_new_product.internal_return_request',
        'hrp_new_product.internal_return_request_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('hrp_new_product.act_internal_return_request')
    def do_create_(self, action):
        new_product = Pool().get('hrp_new_product.new_return')

        data = {}
        for state_name,state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        Move = data['start']['moves']
        Date_ = Pool().get('ir.date')
        Product = Pool().get('product.product')
        MOVE = Pool().get('hrp_new_product.new_return')
        list = []
        scrap = []
        if data['start']['starts'] == '06':
            pass
        elif data['start']['starts'] == None:
            pass
        else:
            scrap.append(('drug_type', '=', data['start']['starts']))
        return_drug = MOVE.search(scrap)
        for i in return_drug:
            dict = {}
            dict['product'] = i.product.id
            with Transaction().set_context(stock_date_end=Date_.today()):
                quantities = Product.products_by_location([i.to_location.id], [i.product.id], with_childs=True)
            if quantities.values():
                return_quantity = [v for v in quantities.values()][0]
            else:
                return_quantity = 0
            if return_quantity <= 0:
                pass
            else:
                dict['return_quantity'] = return_quantity
                list.append(dict)
        now_data = sorted(list,key = lambda x:(x['product'],x['return_quantity']),reverse=False)
        list_compare = []
        for each in Move:
            dict_compare = {}
            dict_compare['product'] = each['product']
            dict_compare['return_quantity'] = each['return_quantity']
            list_compare.append(dict_compare)
        before_data = sorted(list_compare,key = lambda x:(x['product'],x['return_quantity']),reverse=False)

        if before_data == now_data:
            for each in Move:
                if each['examine'] == '02':
                    New_product = new_product.search([
                        ('product','=',each['product']),
                        ('from_location','=',each['from_location']),
                    ])
                    dict = {}
                    if each['can_return_quantity'] == None:
                        return self.raise_user_error(u'已审核的数量不能为空')
                    if each['return_quantity'] < each['can_return_quantity']:
                        return self.raise_user_error(u'审核数量大于请退数量')
                    else:
                        dict['can_return_quantity'] = each['can_return_quantity']#产品的请领数量
                        dict['examine'] = '02'#产品的请领数量
                        new_product.write(New_product,dict)

                elif each['examine'] == '01':
                    New_product = new_product.search([
                        ('product','=',each['product']),
                        ('from_location','=',each['from_location']),
                    ])
                    dict = {}
                    dict['can_return_quantity'] = each['can_return_quantity']#产品的请领数量
                    dict['examine'] = '01'
                    new_product.write(New_product,dict)
        else:
            return self.raise_user_error(u'数据有所更新，请您退出该界面重新进行审核')
        return action,{}
