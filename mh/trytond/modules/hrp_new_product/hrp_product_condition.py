# coding:utf-8
from trytond.model import ModelView
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = ['ProductCondition', 'ProductConditionWizard']

class ProductCondition(ModelView):
    """Product Condition"""
    __name__ = 'hrp_new_product.product_condition'


class ProductConditionWizard(Wizard):
    """Product Condition Wizard"""
    __name__ = 'hrp_new_product.product_condition_wizard'

    start = StateView('hrp_new_product.product_condition',
                      'hrp_new_product.product_condition_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Open', 'open', 'tryton-ok', default=True),
                      ])
    open = StateAction('hrp_new_product.hrp_new_product_act_new_product')

    def do_open(self, action, each=None):
        pool = Pool()
        UomCategory = pool.get('product.category')
        Hrp_Order = pool.get('hrp_order_point.purchaser_reference')
        OrderPoint = pool.get('stock.order_point')
        PurchaseNewProduct = pool.get("hrp_new_product.new_product")
        orderpoints = OrderPoint.search([
            ('type', '=', 'internal')
        ])
        Date = Pool().get('ir.date')
        Product = pool.get('product.product')
        delete_move = PurchaseNewProduct.search([])
        PurchaseNewProduct.delete(delete_move)

        for orderpoint in orderpoints:
            order_product_id = []
              # 订货点产品id
            new_product_id = []  #
            try:
                party = orderpoint.product.template.product_suppliers[0].party.id
            except:
                party = None
            unit_price = orderpoint.product.cost_price
            # warehouse_location = orderpoint.warehouse_location
            retrieve_the_code = orderpoint.retrieve_the_code
            secondary = orderpoint.secondary
            storage_location = orderpoint.provisioning_location.id  # 来自库存低
            provisioning_location = orderpoint.storage_location.id  # 到达库存地
            product = orderpoint.product.id  # 产品
            interim = orderpoint.product.interim  # 产品

            hrp_order = Hrp_Order.search([
                ('warehouse', '=', secondary),
                ('product', '=', product),
            ])
            if hrp_order:
                seven_days = hrp_order[0].seven_days
            else:
                seven_days = 0
            purchase_new = OrderPoint.search([
                ('storage_location', '=', provisioning_location),
            ])
            if purchase_new:
                for i in purchase_new:
                    order_product_id.append(i.product.id)
            categories = [i.id for i in orderpoint.product.categories]
            uom_category = UomCategory.search([('id', '=', categories[0])])
            uom_name = uom_category[0].name
            code = orderpoint.product.code  # 编码
            drug_specifications = orderpoint.product.drug_specifications  # 规格
            a_charge = orderpoint.product.template.a_charge  # 件装量
            is_direct_sending = orderpoint.product.template.is_direct_sending  # 直送
            unit = orderpoint.unit.id  # 单位
            with Transaction().set_context(stock_date_end=Date.today()):
                quantities = Product.products_by_location([provisioning_location], [product], with_childs=True)
            if quantities.values():
                stock_level = [v for v in quantities.values()][0]
            else:
                stock_level = 0
            proposal = seven_days - stock_level

            lv = {}
            lv['drug_specifications'] = drug_specifications
            lv['stock_level'] = int(stock_level)
            # lv['warehouse_location'] = warehouse_location
            if uom_name == u'中成药':
                lv['drug_type'] = '01'
            if uom_name == u'中草药':
                lv['drug_type'] = '02'
            if uom_name == u'原料药':
                lv['drug_type'] = '04'
            if uom_name == u'敷药':
                lv['drug_type'] = '05'
            if uom_name == u'西药':
                lv['drug_type'] = '00'
            if uom_name == u'颗粒中':
                lv['drug_type'] = '03'
            if uom_name == u'同位素':
                lv['drug_type'] = '07'
            if uom_name == '':
                lv['drug_type'] = '06'
            lv['product'] = product
            lv['code'] = code
            if a_charge == None:
                lv['a_charge'] = ''
            else:
                lv['a_charge'] = str(a_charge)
            lv['from_location'] = storage_location
            lv['retrieve_the_code'] = str(retrieve_the_code)
            lv['to_location'] = provisioning_location
            lv['is_direct_sending'] = is_direct_sending
            lv['unit_price'] = unit_price
            lv['uom'] = unit
            lv['outpatient_7days'] = seven_days
            lv['party'] = party  # 供应商
            lv['proposal'] = proposal  # 建议采购量
            if interim == '1' or '00':
                lv['interim'] = '1'
            elif interim == '01':
                lv['interim'] = '2'
            else:
                lv['interim'] = interim
            PurchaseNew = PurchaseNewProduct.search([
                ('to_location', '=', provisioning_location),
                ('product', '=', product)
            ])
            if PurchaseNew:
                PurchaseNewProduct.write(PurchaseNew, lv)
            else:
                PurchaseNewProduct.create([lv])

            # PurchaseNew = PurchaseNewProduct.search([
            #     ('to_location', '=', provisioning_location),
            # ])
            # if PurchaseNew:
            #     for i in PurchaseNew:
            #         new_product_id.append(i.product.id)
            # delete_product_id = [delete_id for delete_id in new_product_id if delete_id not in order_product_id]
            # if delete_product_id == []:
            #     pass
            # else:
            #     for i in delete_product_id:
            #         delete_move = PurchaseNewProduct.search([
            #             ('to_location', '=', provisioning_location),
            #             ('product', '=', i)
            #         ])
            #         PurchaseNewProduct.delete(delete_move)
        return action, {}
