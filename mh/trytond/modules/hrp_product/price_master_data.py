# -*- coding: UTF-8 -*-
import decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.party.party import DEPENDS, STATES
from trytond.modules.timesheet_cost import price_digits
from trytond.pool import Pool
from trytond.config import config
from trytond.transaction import Transaction

__all__ = ['PriceData']


def self(args):
    pass


class PriceData(ModelSQL, ModelView):
    """Pricedata"""
    __name__ = "price_master_datas.pricedata"

    product_name = fields.Char('product_name', select=True)  # 产品名称
    product_code = fields.Char('product_code', select=True)  # 药品编码
    retrieve_the_code = fields.Many2One('product.product', 'retrieve_the_code', required=True, select=True)
    code = fields.Function(fields.Char("Code", size=None, select=True, states=STATES,
                                       depends=DEPENDS), 'get_code', 'set_code')
    name = fields.Function(fields.Char("Name", size=None, required=False, translate=True,
                                       select=True), "get_name", "set_name")
    attach = fields.Char('attach', select=True)
    drug_specifications = fields.Char('drug_specifications', select=True, required=False)
    cost_price = fields.Numeric('cost_price', select=True, digits=price_digits)
    list_price = fields.Numeric('list_price', select=True, digits=price_digits)
    new_cost_price = fields.Float('new_cost_price', select=True, required=True, digits=price_digits)
    new_list_price = fields.Float('new_list_price', select=True, required=True, digits=price_digits)
    modify_reason = fields.Selection([
        ('00', u'来药单'),
        ('01', u'海虹药通'),
    ], 'Modify_reason', select=True)
    effective_date = fields.Date('effective_date', select=True, required=True)

    price_digits = (16, config.getint('product', '', default=4))  # 小数点保留问题

    @classmethod
    def delete(cls, records):
        return cls.raise_user_error(u'历史单据不允许删除')  # 错误信息弹框提示

    @classmethod
    def write(cls, records, values, *args):
        return cls.raise_user_error(u'历史单据不允许修改')

    @classmethod
    def create(cls, vlist):
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        location_id = UserId.get_warehouse_frozen_id()
        # Config = Pool().get('purchase.configuration')
        # config = Config(1)  # 库存地配置
        # location_id = [config.hospital.id,config.outpatient_service.id,config.warehouse.id,config.medical.id,config.endoscopic.id,config.preparation.id,config.ward.id,config.herbs.id]
        price_content = Pool().get('hrp_report.price_profit_loss_content')
        UomCategory = Pool().get('product.category')
        Date = Pool().get('ir.date')
        today = str(Date.today())
        price = Pool().get("product.template")
        product = Pool().get("product.product")
        if str(vlist[0]['effective_date']) == today:
            product_id = vlist[0]['retrieve_the_code']
            Product = product.search([('id', '=', product_id)])
            product_template_id = Product[0].template.id
            New = price.search([
                ('id', '=', product_template_id)
            ])
            if New:
                lvc = {'list_price': vlist[0]['new_list_price'], 'cost_price': vlist[0]['new_cost_price']}
                price.write(New, lvc)
                content = []
                for each in location_id:
                    content_dict = {}
                    with Transaction().set_context(stock_date_end=Date.today()):
                        quantities = product.products_by_location([each['warehouse']], [product_id], with_childs=True)
                        if quantities.values():
                            stock_level_warehouse = [v for v in quantities.values()][0]
                        else:
                            stock_level_warehouse = 0
                    with Transaction().set_context(stock_date_end=Date.today()):
                        quantities = product.products_by_location([each['freeze']], [product_id], with_childs=True)
                        if quantities.values():
                            stock_level_freeze = [v for v in quantities.values()][0]
                        else:
                            stock_level_freeze = 0
                        stock_level = stock_level_warehouse+stock_level_freeze
                        party = Product[0].product_suppliers
                        if party:
                            party = party[0].party.name
                        else:
                            party = ''
                        categories = [i.id for i in Product[0].categories]
                        uom_category = UomCategory.search([('id', '=', categories[0])])
                        uom_name = uom_category[0].name
                        if uom_name == u'西药':
                            content_dict['drug_type'] = '00'
                        if uom_name == u'中成药':
                            content_dict['drug_type'] = '01'
                        if uom_name == u'中草药':
                            content_dict['drug_type'] = '02'
                        if uom_name == u'颗粒中':
                            content_dict['drug_type'] = '03'
                        if uom_name == u'原料药':
                            content_dict['drug_type'] = '04'
                        if uom_name == u'敷药':
                            content_dict['drug_type'] = '05'
                        if uom_name == u'同位素':
                            content_dict['drug_type'] = '07'
                        content_dict['location'] = each['warehouse']
                        content_dict['code'] = vlist[0]['product_code']
                        content_dict['product'] = vlist[0]['product_name']
                        content_dict['drug_specifications'] = vlist[0]['drug_specifications']
                        content_dict['list_price'] = vlist[0]['list_price']
                        content_dict['cost_price'] = vlist[0]['cost_price']
                        content_dict['new_list_price'] = vlist[0]['new_list_price']
                        content_dict['new_cost_price'] = vlist[0]['new_cost_price']
                        content_dict['inventory'] = float(stock_level)
                        content_dict['effective_date'] = today
                        content_dict['party'] = party
                        content_dict['uom'] = Product[0].template.default_uom.id
                        content_dict['price_profit_loss'] = decimal.Decimal(str(stock_level))*(decimal.Decimal(str(vlist[0]['new_cost_price'])) - vlist[0]['cost_price'])
                        content_dict['price_list_profit_loss'] = decimal.Decimal(str(stock_level))*(decimal.Decimal(str(vlist[0]['new_list_price'])) - vlist[0]['list_price'])
                        content.append(content_dict)
                price_content.create(content)
            else:
                pass
        return super(PriceData, cls).create(vlist)

    @classmethod
    def create_profit_loss(cls, Pricedata):
        for price_data in Pricedata:
            UserId = Pool().get('hrp_internal_delivery.test_straight')
            location_id = UserId.get_warehouse_frozen_id()
            price_content = Pool().get('hrp_report.price_profit_loss_content')
            UomCategory = Pool().get('product.category')
            Date = Pool().get('ir.date')
            today = str(Date.today())
            product = Pool().get('product.product')
            content = []
            for each in location_id:
                dict = {}
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = product.products_by_location([each['warehouse']], [price_data.retrieve_the_code.id], with_childs=True)
                    if quantities.values():
                        stock_level_warehouse = [v for v in quantities.values()][0]
                    else:
                        stock_level_warehouse = 0
                with Transaction().set_context(stock_date_end=Date.today()):
                    quantities = product.products_by_location([each['freeze']], [price_data.retrieve_the_code.id],
                                                              with_childs=True)
                    if quantities.values():
                        stock_level_freeze = [v for v in quantities.values()][0]
                    else:
                        stock_level_freeze = 0
                    stock_level = stock_level_warehouse + stock_level_freeze
                    party = price_data.retrieve_the_code.product_suppliers
                    if party:
                        party = party[0].party.name
                    else:
                        party = ''
                    categories = [i.id for i in price_data.retrieve_the_code.categories]
                    uom_category = UomCategory.search([('id', '=', categories[0])])
                    uom_name = uom_category[0].name
                    if uom_name == u'西药':
                        dict['drug_type'] = '00'
                    if uom_name == u'中成药':
                        dict['drug_type'] = '01'
                    if uom_name == u'中草药':
                        dict['drug_type'] = '02'
                    if uom_name == u'颗粒中':
                        dict['drug_type'] = '03'
                    if uom_name == u'原料药':
                        dict['drug_type'] = '04'
                    if uom_name == u'敷药':
                        dict['drug_type'] = '05'
                    if uom_name == u'同位素':
                        dict['drug_type'] = '07'
                    dict['location'] = each['warehouse']
                    dict['code'] = price_data.product_code
                    dict['product'] = price_data.product_name
                    dict['drug_specifications'] = price_data.drug_specifications
                    dict['list_price'] = price_data.list_price
                    dict['cost_price'] = price_data.cost_price
                    dict['new_list_price'] = price_data.new_list_price
                    dict['new_cost_price'] = price_data.new_cost_price
                    dict['inventory'] = float(stock_level)
                    dict['effective_date'] = today
                    dict['party'] = party
                    dict['uom'] = price_data.retrieve_the_code.template.default_uom.id
                    dict['price_profit_loss'] = decimal.Decimal(str(stock_level)) * (
                    decimal.Decimal(str(price_data.new_cost_price)) - price_data.cost_price)
                    dict['price_list_profit_loss'] = decimal.Decimal(str(stock_level)) * (
                    decimal.Decimal(str(price_data.new_list_price)) - price_data.list_price)
                    content.append(dict)
            price_content.create(content)



    @fields.depends('retrieve_the_code')
    def on_change_retrieve_the_code(self):
        if self.retrieve_the_code != '':
            try:
                Retrieve = self.retrieve_the_code.name
                Attach = self.retrieve_the_code.attach
                Code = self.retrieve_the_code.code
                Drug_specifications = self.retrieve_the_code.drug_specifications
                Cost_price = self.retrieve_the_code.cost_price
                List_price = self.retrieve_the_code.list_price
                hrp = Pool().get('product.product')
                HRP = hrp.search([
                    ('id', '=', self.retrieve_the_code.id)
                ])
                if HRP:
                    try:
                        self.product_name = Retrieve
                        self.product_code = Code
                        self.name = Retrieve
                        self.attach = Attach
                        self.code = Code
                        self.drug_specifications = str(Drug_specifications)
                        self.cost_price = Cost_price
                        self.list_price = List_price
                    except:
                        pass
            except:
                pass

    def get_code(self, name):
        pool = Pool()
        try:
            product_templates = pool.get('product.product')
            product_template = product_templates.search([
                ("id", "=", int(self.retrieve_the_code.mark.id))
            ])
            code = product_template[0].code
        except:
            return None
        return code

    def get_name(self, name):
        pool = Pool()
        try:
            product_templates = pool.get('product.template')
            product_template = product_templates.search([
                ("id", "=", int(self.retrieve_the_code.mark.id))
            ])
            name = product_template[0].name
        except:
            return None
        return name

    @classmethod
    def set_code(cls, set_code, name, value):
        pass

    @classmethod
    def set_name(cls, set_name, name, value):
        pass

    @classmethod
    def write_price(cls):
        Price = Pool().get('price_master_datas.pricedata')
        with Transaction().set_context(user=1):
            Date = Pool().get('ir.date')
            today = str(Date.today())
            pricedata = Pool().get('price_master_datas.pricedata')
            Pricedata = pricedata.search([
                ('effective_date', '=', today)
            ])
            price = Pool().get("product.template")
            if Pricedata:
                for i in Pricedata:
                    Retri = i.retrieve_the_code.template.id
                    New_cost_price = i.new_cost_price
                    New_list_price = i.new_list_price
                    New = price.search([
                        ('id', '=', Retri)
                    ])
                    if New:
                        lvc = {'list_price': New_list_price, 'cost_price': New_cost_price}
                        price.write(New, lvc)

                    else:
                        pass
                Price.create_profit_loss(Pricedata)

