# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import decimal
from decimal import *
from datetime import *

import arrow
import operator

from trytond.modules.company import CompanyReport
from trytond.wizard import Wizard, StateView, StateAction, Button, StateTransition
from trytond.pyson import Eval, Bool, Not, Equal
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.config import config

__all__ = ['Inventory', 'InventoryLines', 'InventoryReport', 'InventoryTwo', 'InventoryTwoLines', 'InventoryTwoReport',
           'ModifyTheInventory', 'ModifyTheInventorylines', 'ModifyThe', 'InventoryTime']

price_digits = (16, config.getint('product', 'price_decimal', default=4))


class InventoryTwoReport(CompanyReport):
    "InventoryTwoReport"
    __name__ = 'hrp_inventory.inventory_two'


class InventoryReport(CompanyReport):
    "Inventory"
    __name__ = 'hrp_inventory.inventory'


class InventoryTime(ModelSQL, ModelView):
    "InventoryTime"
    __name__ = 'hrp_inventory.inventory_time'
    start_time = fields.DateTime('start_time', select=True)
    end_time = fields.DateTime('end_time', select=True)
    inventory = fields.Many2One('hrp_inventory.inventory_two', 'inventory', select=True)

    @classmethod
    def __setup__(cls):
        super(InventoryTime, cls).__setup__()
        cls._order = [('id', 'DESC')]
    def get_rec_name(self, name):
        return self.start_time.strftime('%Y-%m-%d %H:%M:%S')


class Inventory(ModelSQL, ModelView, Workflow):
    "Inventory"
    __name__ = "hrp_inventory.inventory"

    inventory_time = fields.DateTime('Inventory Time', select=True, readonly=True, required=False)
    warehouse = fields.Many2One('stock.location', 'Warehouse', select=True, readonly=True)
    categories = fields.Many2One('product.category', 'Categories')
    varieties_num = fields.Float('Varieties Num', readonly=True)
    Inventory_details = fields.One2Many('hrp_inventory.inventory_lines', 'inventory', 'Inventory details', states={
        'readonly': (Eval('state') == 'done'),
    }, )
    amount = fields.Numeric('amount', readonly=True, digits=price_digits)
    state = fields.Selection([
        ('draft', u'起草'),
        ('processing', u'处理中'),
        ('done', u'完成')
    ], 'State', readonly=True, required=True, select=True)
    print_warehouse = fields.Boolean('print_warehouse')

    @classmethod
    def __setup__(cls):
        super(Inventory, cls).__setup__()
        cls._buttons.update({
            'balance_of_inventory': {
                'readonly': Eval('state') != 'processing',
            },
            'create_the_inventory': {
                'readonly': Eval('state') != 'draft',
            },
        })
        cls._order[0] = ('id', 'DESC')

    @staticmethod
    def default_print_warehouse():
        return False

    @staticmethod
    def default_state():
        return 'draft'

    # @staticmethod
    # def default_inventory_time():
    #     times = arrow.utcnow().to('00:00').datetime
    #     return times

    @staticmethod
    def default_varieties_num():
        return 0

    @staticmethod
    def default_amount():
        return decimal.Decimal('0.00')

    @staticmethod
    def default_warehouse():
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        warehouse = config.warehouse.id
        return warehouse

    @classmethod
    @ModelView.button
    def create_the_inventory(self, inventories):
        Product = Pool().get('product.product')
        Inventory = Pool().get('hrp_inventory.inventory')
        InventoryLines = Pool().get('hrp_inventory.inventory_lines')
        Date = Pool().get('ir.date')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        from_location = config.warehouse.storage_location.id
        freeze_id = config.warehouse.freeze_location.id
        ids = inventories[0].id
        category = inventories[0].categories.id
        Purchase = Pool().get('purchase.purchase')
        purchase = Purchase.search([('id', '=', 228)])
        Purchase.write(purchase, {'internal_order': '123'})
        with Transaction().set_context(stock_date_end=Date.today()):
            warehouse_pbl = Product.products_by_location([from_location], with_childs=True)
            amount_num = 0
            freeze_num = 0
            product_id = 0
            lines = 1
            for key, value in warehouse_pbl.iteritems():
                product = Product.search([('id', '=', key[1])])
                if not product:
                    continue
                categories = product[0].template.categories[0].id
                if category != categories:
                    continue
                freeze_ids = product[0].id
                code = product[0].code
                name = product[0].template.name
                drug_specifications = product[0].template.drug_specifications
                cost_pice = product[0].template.cost_price
                warehouse_num = value
                freeze_pbl = Product.products_by_location([freeze_id], [freeze_ids], with_childs=True)
                for freeze_key, freeze_value in freeze_pbl.iteritems():
                    freeze_num = freeze_value
                amount = decimal.Decimal(str((warehouse_num + freeze_num) * round(cost_pice, 3)))
                amount_num += amount
                to_create = {
                    u'lines': lines,
                    u'inventory': ids,
                    u'product': product[0].id,
                    u'code': code,
                    u'name': name,
                    u'uom': product[0].default_uom.id,
                    u'wholesale_amount': amount,
                    u'cost_pice': cost_pice,
                    u'warehouse_num': warehouse_num,
                    u'warehouse_real_num': warehouse_num,
                    u'freeze_real_num': freeze_num,
                    u'freeze_num': freeze_num,
                    u'references_to': freeze_num + warehouse_num,
                    u'drug_specifications': drug_specifications,
                    u'differences_why': '00'}
                InventoryLines.create([to_create])
                lines += 1
                freeze_num = 0
            Inventory.write(inventories, {'varieties_num': (lines - 1), 'amount': amount_num, 'state': 'processing',
                                          'inventory_time': arrow.utcnow().to('00:00').datetime})

    @classmethod
    @ModelView.button
    def balance_of_inventory(self, inventories):
        Product = Pool().get('product.product')
        Lot = Pool().get('stock.lot')
        Date = Pool().get('ir.date')
        Inventories = Pool().get('stock.inventory')
        InventoryLine = Pool().get('stock.inventory.line')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        from_location = config.warehouse.storage_location.id
        freeze_id = config.return_of.id
        date = inventories[0].inventory_time.strftime('%Y-%m-%d')
        lines = inventories[0].Inventory_details
        location_list = []
        freeze_list = []
        for location in lines:
            if location.warehouse_num != location.warehouse_real_num:
                location_list.append(location)
            if location.freeze_num != location.freeze_real_num:
                freeze_list.append(location)
        if location_list != []:
            inventory = Inventories.create([{
                u'company': Transaction().context.get('company'),
                u'lines': [],
                u'number': u'',
                u'location': from_location,
                u'date': date,
                u'lost_found': 7
            }])
            inventory_id = inventory[0].id
            Inventories.complete_lines(inventory)
            for loc in location_list:
                try:
                    lot = loc.lot_warehouse
                except:
                    lot = self.get_lot(from_location, loc.product.id)
                product_id = loc.product.id
                inventory_line = InventoryLine.search([('inventory', '=', inventory_id),
                                                       ('product', '=', product_id),
                                                       ('lot', '=', lot)])
                if inventory_line:
                    InventoryLine.write(inventory_line, {'lot': lot, 'quantity': loc.warehouse_real_num})
            Inventories.confirm(inventory)
        if freeze_list != []:
            inventory_freeze = Inventories.create([{
                u'company': Transaction().context.get('company'),
                u'lines': [],
                u'number': u'',
                u'location': freeze_id,
                u'date': date,
                u'lost_found': 7
            }])
            inventory_ids = inventory_freeze[0].id
            Inventories.complete_lines(inventory_freeze)
            for loca in freeze_list:
                try:
                    lots = loca.lot_freeze
                except:
                    lots = self.get_lot(freeze_id, loca.product.id)
                inventory_lines = InventoryLine.search([('inventory', '=', inventory_ids),
                                                        ('product', '=', loca.product.id),
                                                        ('lot', '=', lots)])
                if inventory_lines:
                    InventoryLine.write(inventory_lines, {'lot': lots, 'quantity': loca.warehouse_real_num})
            Inventories.confirm(inventory_freeze)
        Inventory.write(inventories, {'state': 'done'})

    @classmethod
    def get_lot(cls, location, product):
        Product = Pool().get('product.product')
        Lot = Pool().get('stock.lot')
        Date = Pool().get('ir.date')
        lists = []
        with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location], [product], with_childs=True,
                                                           grouping=('product', 'lot'))
            # key = warehouse_quant.keys()
            for key, value in warehouse_quant.items():
                if value != 0.0:
                    if key[-1] != None:
                        lists.append(key[-1])
            lot_list = []
            if lists != []:
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
                return lots_list[0]

    @classmethod
    def delete(cls, records):
        cls.raise_user_error(u'盘点详情不允许删除',
                             u'盘点详情不允许删除')


class InventoryLines(ModelSQL, ModelView):
    "Inventory Lines"
    __name__ = "hrp_inventory.inventory_lines"

    inventory = fields.Many2One('hrp_inventory.inventory', 'Inventory_details', required=False, ondelete='CASCADE')
    lines = fields.Integer('Line', select=True, readonly=True)
    product = fields.Many2One('product.product', 'Product', help='Drugs in code')
    code = fields.Char('Code', readonly=True)
    name = fields.Char('Name', readonly=True)
    uom = fields.Many2One('product.uom', 'Default UOM', required=False, readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    warehouse_num = fields.Float('Warehouse Num', readonly=True)  # 非限制(账面)
    freeze_num = fields.Float('Freeze Num', readonly=True)  # 冻结(账面)
    cost_pice = fields.Numeric('Cost Price', digits=price_digits, readonly=True)
    wholesale_amount = fields.Numeric('Wholesale amount', readonly=True, digits=price_digits)  # 批发金额
    warehouse_real_num = fields.Float('Warehouse Real Num', )  # 非限制(实盘)
    freeze_real_num = fields.Float('Freeze Real Num', )  # 冻结(实盘)
    references_to = fields.Float('References to', readonly=True)
    lot_warehouse = fields.Many2One('stock.lot', 'Lot Warehouse', domain=[('product', '=', Eval('product'))],
                                    depends=['product'])
    lot_freeze = fields.Many2One('stock.lot', 'Lot Freeze', domain=[('product', '=', Eval('product'))],
                                 depends=['product'])
    differences_why = fields.Selection([('00', u''), ('01', u'工作失误')], 'Differences Why', required=False)
    note = fields.Char('Note')

    @fields.depends('warehouse_num', 'warehouse_real_num', 'freeze_real_num', 'lot_warehouse', 'references_to',
                    'product', 'inventory')
    def on_change_warehouse_real_num(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        lists = []
        Lot = Pool().get('stock.lot')
        try:
            self.references_to = self.warehouse_real_num + self.freeze_real_num
        except TypeError:
            self.references_to = self.warehouse_real_num
        if self.warehouse_num < self.warehouse_real_num:
            sdsdd = self.inventory
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([self.inventory.warehouse], [self.product.id],
                                                               with_childs=True, grouping=('product', 'lot'))
                # key = warehouse_quant.keys()
                for key, value in warehouse_quant.items():
                    if value != 0.0:
                        if key[-1] != None:
                            lists.append(key[-1])
                lot_list = []
                if lists != []:
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
                    self.lot_warehouse = lots_list[0]
                    self.differences_why = '01'
                else:
                    pass
        elif self.warehouse_num > self.warehouse_real_num:
            self.differences_why = '01'
        else:
            pass

    @fields.depends('freeze_num', 'freeze_real_num', 'lot_freeze', 'references_to', 'warehouse_real_num', 'product',
                    'inventory')
    def on_change_freeze_real_num(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        freeze_id = config.return_of.id
        lists = []
        Lot = Pool().get('stock.lot')
        try:
            self.references_to = self.warehouse_real_num + self.freeze_real_num
        except TypeError:
            self.references_to = self.freeze_real_num
        if self.freeze_num < self.freeze_real_num and self.freeze_num != 0:
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([freeze_id], [self.product.id], with_childs=True,
                                                               grouping=('product', 'lot'))
                for key, value in warehouse_quant.items():
                    if value != 0.0:
                        if key[-1] != None:
                            lists.append(key[-1])
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
            self.lot_freeze = lots_list[0]
        elif self.freeze_num > self.freeze_real_num:
            self.differences_why = '01'
        else:
            pass


class InventoryTwo(ModelSQL, ModelView, Workflow):
    "Inventory Two"
    __name__ = "hrp_inventory.inventory_two"

    inventory_time = fields.DateTime('Inventory Time', select=True, readonly=True, required=False)
    warehouse = fields.Many2One('stock.location', 'Warehouse', readonly=False, required=True,
                                domain=[('type', '=', 'warehouse')], select=True
                                , states={'readonly': (Eval('state') != 'draft')})
    categories = fields.Many2One('product.category', 'Categories', select=True, required=False, states={
        'readonly': (Eval('state') != 'draft')})
    categories_two = fields.Selection([
        (u'中成药', u'中成药'),
        (u'中草药', u'中草药'),
        (u'原料药', u'原料药'),
        (u'敷药', u'敷药'),
        (u'西药', u'西药'),
        (u'颗粒中', u'颗粒中'),
        (u'同位素', u'同位素'),
        (u'全部', u'全部')], 'categories_two', select=True, required=True, states={
        'readonly': (Eval('state') != 'draft')})
    varieties_num = fields.Float('Varieties Num', readonly=True)
    Inventory_details = fields.One2Many('hrp_inventory.inventory_two_lines', 'inventory', 'Inventory details',
                                        readonly=True)
    amount = fields.Numeric('amount', readonly=True, digits=price_digits)
    state = fields.Selection([
        ('draft', u'起草'),
        ('processing', u'处理中'),
        ('done', u'完成')
    ], 'State', readonly=True, required=True, select=True)
    drug_inventory = fields.Boolean('drug_inventory')
    shelves_inventory = fields.Boolean('shelves_inventory')
    print_warehouse = fields.Boolean('print_warehouse')
    print_one = fields.Boolean('print_one')
    print_two = fields.Boolean('print_two')

    @classmethod
    def __setup__(cls):
        super(InventoryTwo, cls).__setup__()
        cls._buttons.update({
            'balance_of_inventory': {
                'readonly': Eval('state') != 'processing',
            },
            'create_wizard': {
                'readonly': Eval('state') != 'processing',
            },
            'create_the_inventory': {
                'readonly': Eval('state') != 'draft',
            },
        })
        cls._order[0] = ('id', 'DESC')

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_warehouse():
        UserId = Pool().get('hrp_internal_delivery.test_straight')
        return UserId.get_user_warehouse()

    @staticmethod
    def default_drug_inventory():
        return True

    @fields.depends('drug_inventory', 'shelves_inventory')
    def on_change_drug_inventory(self, name=None):
        if self.drug_inventory:
            self.shelves_inventory = False
        else:
            self.shelves_inventory = True

    @fields.depends('print_warehouse', 'warehouse')
    def on_change_print_warehouse(self, name=None):
        if self.warehouse:
            Config = Pool().get('purchase.configuration')
            config = Config(1)
            if self.warehouse == config.warehouse.id:
                self.print_warehouse = True

    @fields.depends('drug_inventory', 'shelves_inventory')
    def on_change_shelves_inventory(self, name=None):
        if self.shelves_inventory:
            self.drug_inventory = False
        else:
            self.drug_inventory = True

    @staticmethod
    def default_varieties_num():
        return 0

    @staticmethod
    def default_amount():
        return decimal.Decimal('0.00')

    @classmethod
    @ModelView.button
    def create_the_inventory(self, inventories):
        ProductQuantity = Pool().get('product_quantity')
        Product = Pool().get('product.product')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        UomCategory = Pool().get('product.category')
        Inventory = Pool().get('hrp_inventory.inventory_two')
        InventoryLines = Pool().get('hrp_inventory.inventory_two_lines')
        AvailableMedicine = Pool().get("hrp_inventory.available_medicine_line")
        Date = Pool().get('ir.date')
        from_location = inventories[0].warehouse.storage_location.id
        freeze_id = inventories[0].warehouse.freeze_location.id
        preparation = config.preparation.storage_location.id
        warehouse = config.warehouse.storage_location.id
        inventory_id = inventories[0].id
        if inventories[0].categories_two != u'全部':
            category_all = [inventories[0].categories_two]
        else:
            category_all = [u'西药', u'中成药']
        category = UomCategory.search([('name', 'in', category_all)])
        category_ids = [ids.id for ids in category]
        # try:
        if True:
            amount_num = 0
            freeze_num = 0
            lines = 1
            with Transaction().set_context(stock_date_end=Date.today()):
                warehouse_pbl = Product.products_by_location([from_location], with_childs=True)
                to_create_list = []
                print_type = {}
                for key, value in warehouse_pbl.iteritems():
                    product = Product.search([('id', '=', key[1])])
                    if product == []:
                        continue
                    categories = product[0].template.categories[0].id
                    if categories not in category_ids:
                        continue
                    freeze_ids = product[0].id
                    code = product[0].code
                    name = product[0].template.name
                    drug_specifications = product[0].template.drug_specifications
                    cost_pice = product[0].template.cost_price
                    warehouse_num = value
                    freeze_pbl = Product.products_by_location([freeze_id], [freeze_ids], with_childs=True)
                    for freeze_key, freeze_value in freeze_pbl.iteritems():
                        freeze_num = freeze_value
                    if value == 0.0 and freeze_num == 0.0:
                        continue
                    amount = decimal.Decimal(str((warehouse_num + freeze_num) * round(cost_pice, 3)))
                    amount_num += amount.quantize(decimal.Decimal('0.00'))
                    Medicine = AvailableMedicine.search([('warehouse', '=', inventories[0].warehouse.id),
                                                         ('product', '=', product[0].id)])

                    shelves = ''
                    if from_location == preparation or warehouse == from_location:
                        print_type['print_warehouse'] = True
                        product_quantity = ProductQuantity.search(
                            [('product', '=', product[0].id), ('sequence', '=', 1)])
                        uoms = product[0].default_uom.id
                        cost_pices = cost_pice
                        factor = 1
                        if product_quantity:
                            shelves = product_quantity[0].location.name
                    else:
                        print_type['print_one'] = True
                        if Medicine:
                            factor = round((product[0].default_uom.factor * Medicine[0].scattered_uom.rate), 3)  # 单位换算
                            uoms = Medicine[0].scattered_uom.id
                            cost_pices = decimal.Decimal(str(round(cost_pice, 3) / factor)).quantize(
                                decimal.Decimal('0.01'))
                            shelves = Medicine[0].shelves_code
                        else:
                            factor = 1
                            cost_pices = cost_pice
                            uoms = product[0].default_uom.id
                    to_create = {
                        u'shelves': shelves,
                        u'lines': lines,
                        u'inventory': inventory_id,
                        u'warehouse': from_location,
                        U'freeze_warehouse': freeze_id,
                        u'product': product[0].id,
                        u'code': code,
                        u'name': name,
                        u'type': u'balance',
                        u'category': product[0].template.categories[0].id,
                        u'uom': uoms,
                        u'wholesale_amount': amount.quantize(Decimal('0.00')),
                        u'cost_pice': cost_pices.quantize(Decimal('0.00')),
                        u'warehouse_num': float(warehouse_num * factor),
                        u'warehouse_real_num': float(warehouse_num * factor),
                        u'freeze_real_num': float(freeze_num * factor),
                        u'freeze_num': float(freeze_num * factor),
                        u'references_to': float((freeze_num + warehouse_num) * factor),
                        u'drug_specifications': drug_specifications,
                        u'differences_why': '00'}
                    to_create_list.append(to_create)
                    lines += 1
                    freeze_num = 0
                if inventories[0].shelves_inventory:
                    to_create_list = sorted(to_create_list, key=operator.itemgetter('shelves'))
                for create_ in to_create_list:
                    InventoryLines.create([create_])
                inventory_dict = dict({'varieties_num': (lines - 1), 'amount': amount_num, 'state': 'processing',
                                       'inventory_time': arrow.utcnow().to('00:00').datetime}, **print_type)
                Inventory.write(inventories, inventory_dict)
                # except:
                #     self.raise_user_error(u'需要先创建药房盘点单位')

    @classmethod
    @ModelView.button_action('hrp_inventory.wizard_modify_the_inventory')
    def create_wizard(self, inventories):
        pass

    @classmethod
    @ModelView.button
    def balance_of_inventory(self, inventories):
        Uom = Pool().get('product.uom')
        Product = Pool().get('product.product')
        ProductQuantity = Pool().get('product_quantity')
        Lot = Pool().get('stock.lot')
        Inventories = Pool().get('stock.inventory')
        InventoryTime = Pool().get('hrp_inventory.inventory_time')
        InventoryLine = Pool().get('stock.inventory.line')
        InventoryLines = Pool().get('hrp_inventory.inventory_two_lines')
        from_location = inventories[0].warehouse.storage_location.id
        freeze_id = inventories[0].warehouse.freeze_location.id
        Date = Pool().get('ir.date')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        preparation = config.preparation.id
        warehouse = config.warehouse.storage_location.id
        date = inventories[0].inventory_time.strftime('%Y-%m-%d')
        lines = inventories[0].Inventory_details
        print_type = {}
        if from_location == preparation or warehouse == from_location:
            print_type['print_warehouse'] = True
        else:
            print_type['print_one'] = True
        location_list = []
        freeze_list = []
        for location in lines:
            if location.warehouse_num != location.warehouse_real_num and location.state != 'done':
                differences = location.warehouse_real_num - location.warehouse_num
                with Transaction().set_context(stock_date_end=Date.today()):
                    warehouse_pbl = Product.products_by_location([from_location], with_childs=True)
                    quantity = warehouse_pbl[(from_location, location.product.id)]
                    if Uom.compute_qty(location.product.default_uom, quantity, location.uom) + differences >= 0:
                        location_list.append({'location': location, 'differences': differences})
                    else:
                        InventoryLines.write([location], {'state': 'processing'})
            if location.freeze_num != location.freeze_real_num and location.state != 'done':
                differences = location.freeze_real_num - location.freeze_num
                with Transaction().set_context(stock_date_end=Date.today()):
                    warehouse_freeze_id = Product.products_by_location([freeze_id], with_childs=True)
                    quantity = warehouse_freeze_id[(freeze_id, location.product.id)]
                    if Uom.compute_qty(location.product.default_uom, quantity, location.uom) + differences >= 0:
                        freeze_list.append({'location': location, 'differences': differences})
                    else:
                        InventoryLines.write([location], {'state': 'processing'})
        if location_list != []:
            if warehouse != from_location:
                inventory = Inventories.create([{
                    u'company': Transaction().context.get('company'),
                    u'lines': [],
                    u'number': u'',
                    u'location': from_location,
                    u'date': date,
                    u'lost_found': 7
                }])
                inventory_id = inventory[0].id
                Inventories.complete_lines(inventory)
                for loc in location_list:
                    try:
                        lot = [{'id': loc['location'].lot_warehouse.id}]
                    except:
                        lot = self.get_lot(from_location, loc['location'].product.id)
                    product_id = loc['location'].product.id
                    inventory_quantity = loc['differences']
                    for inventory_lot in lot:
                        inventory_line = InventoryLine.search([('inventory', '=', inventory_id),
                                                               ('product', '=', product_id),
                                                               ('lot', '=', inventory_lot['id'])])
                        if inventory_line and inventory_line[0].quantity + inventory_quantity >= 0:
                            InventoryLine.write(inventory_line,
                                                {'lot': inventory_lot['id'],
                                                 'quantity': inventory_line[0].quantity + inventory_quantity})
                            InventoryLines.write([loc['location']], {'state': 'done'})
                            break
                        elif inventory_line and inventory_line[0].quantity + inventory_quantity < 0:
                            inventory_quantity += inventory_line[0].quantity
                            InventoryLine.write(inventory_line, {'lot': inventory_lot['id'], 'quantity': 0})
                        elif inventory_quantity > 0:
                            InventoryLine.create([{'lot': inventory_lot['id'],
                                                   'product': loc['location'].product.id,
                                                   'quantity': inventory_quantity,
                                                   'inventory': inventory_id}])
                Inventories.confirm(inventory)
            else:
                location_wms = []
                complete_lines = []
                lots_lines = []
                inventories_list = []
                for loc in location_list:
                    try:
                        lot = [{'id': loc['location'].lot_warehouse.id}]
                    except:
                        lot = self.get_lot(from_location, loc['location'].product.id)
                    lots_lines.append({'lot': lot, 'differences': loc['differences'], 'inventory': loc})
                    product_quantity = ProductQuantity.search([('product', '=', loc['location'].product.id)])
                    if product_quantity:
                        for loc in product_quantity:
                            location_wms.append({'location': loc.location.id, 'sequence': loc.sequence})
                        location_wms.append({'location': from_location, 'sequence': 9999})
                        location_wmss = []
                        for ids in location_wms:
                            if ids not in location_wmss:
                                location_wmss.append(ids)
                        all_location = sorted(location_wmss, key=operator.itemgetter('sequence'))
                        for locs in all_location:
                            inventory = Inventories.create([{
                                u'company': Transaction().context.get('company'),
                                u'lines': [],
                                u'number': u'',
                                u'location': locs['location'],
                                u'date': date,
                                u'lost_found': 7
                            }])
                            inventories_list.append(inventory)
                            inventory_id = inventory[0].id
                            Inventories.complete_lines(inventory)
                            inventory_line = InventoryLine.search([('inventory', '=', inventory_id)])
                            for linese in inventory_line:
                                complete_lines.append({'inventory_line': linese, 'inventory_id': inventory_id})

                for lot_line in lots_lines:
                    inventory_quantity = lot_line['differences']
                    for one_lot in lot_line['lot']:
                        if inventory_quantity == 0:
                            break
                        mark = True
                        for complete_line in complete_lines:
                            if complete_line['inventory_line'].product == Lot(one_lot['id']).product and \
                                            complete_line['inventory_line'].lot.id == one_lot['id']:
                                mark = False
                                if complete_line['inventory_line'].quantity + inventory_quantity >= 0:
                                    InventoryLine.write([complete_line['inventory_line']],
                                                        {'lot': one_lot['id'], 'quantity': complete_line[
                                                                                               'inventory_line'].quantity + inventory_quantity})
                                    InventoryLines.write([lot_line['inventory']['location']], {'state': 'done'})
                                    inventory_quantity = 0
                                    break
                                elif complete_line['inventory_line'].quantity + inventory_quantity < 0:
                                    inventory_quantity += complete_line['inventory_line'].quantity
                                    InventoryLine.write([complete_line['inventory_line']],
                                                        {'lot': one_lot['id'], 'quantity': 0})
                                elif inventory_quantity > 0:
                                    InventoryLine.create([{'lot': one_lot['id'],
                                                           'product': lot_line['inventory']['location'].product.id,
                                                           'quantity': inventory_quantity,
                                                           'inventory': complete_line['inventory_id']}])
                        if mark:
                            InventoryLine.create([{'lot': one_lot['id'],
                                                   'product': lot_line['inventory']['location'].product.id,
                                                   'quantity': inventory_quantity,
                                                   'inventory': inventories_list[-1][0].id}])
                            # self.raise_user_error()
                for inventory in inventories_list:
                    Inventories.confirm(inventory)
        if freeze_list != []:
            inventory_freeze = Inventories.create([{
                u'company': Transaction().context.get('company'),
                u'lines': [],
                u'number': u'',
                u'location': freeze_id,
                u'date': date,
                u'lost_found': 7
            }])
            inventory_id = inventory_freeze[0].id
            Inventories.complete_lines(inventory_freeze)
            for loca in freeze_list:
                try:
                    lots = [{'id': loca['location'].lot_freeze.id}]
                except:
                    lots = self.get_lot(freeze_id, loca['location'].product.id)
                inventory_quantity = loca['differences']
                for inventory_lot in lots:
                    inventory_lines = InventoryLine.search([('inventory', '=', inventory_id),
                                                            ('product', '=', loca['location'].product.id),
                                                            ('lot', '=', inventory_lot['id'])])
                    if inventory_lines and inventory_lines[0].quantity + inventory_quantity > 0:
                        InventoryLine.write(inventory_lines, {'lot': inventory_lot['id'], 'quantity': inventory_lines[
                                                                                                          0].quantity + inventory_quantity})
                        InventoryLines.write([loca['location']], {'state': 'done'})
                        break
                    elif inventory_lines and inventory_lines[0].quantity + inventory_quantity < 0:
                        InventoryLine.write(inventory_lines, {'lot': inventory_lot['id'], 'quantity': 0})
                        inventory_quantity += inventory_lines[0].quantity
                    elif inventory_quantity > 0:
                        InventoryLine.create([{'lot': inventory_lot['id'],
                                               'product': loca['location'].product.id,
                                               'quantity': inventory_quantity,
                                               'inventory': inventory_id}])

            Inventories.confirm(inventory_freeze)
        state = 'done'
        for location in lines:
            if location.state == 'processing':
                state = 'processing'
        InventoryTwo.write(inventories, {'state': state})
        if state == 'done':
            InventoryTime.create([{'start_time': inventories[0].inventory_time,
                                   'end_time': inventories[0].write_date,
                                   'inventory': inventories[0].id}])

    @classmethod
    def get_lot(cls, location, product):
        Product = Pool().get('product.product')
        Lot = Pool().get('stock.lot')
        Date = Pool().get('ir.date')
        lists = []
        with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
            warehouse_quant = Product.products_by_location([location], [product], with_childs=True,
                                                           grouping=('product', 'lot'))
            # key = warehouse_quant.keys()
            for key, value in warehouse_quant.items():
                if value != 0.0:
                    if key[-1] != None:
                        lists.append(key[-1])
            lot_list = []
            if lists != []:
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
                return lots_list


class InventoryTwoLines(ModelSQL, ModelView):
    "Inventory Two Lines"
    __name__ = "hrp_inventory.inventory_two_lines"

    shelves = fields.Char('shelves')
    freeze_warehouse = fields.Many2One('stock.location', 'Warehouse')
    warehouse = fields.Many2One('stock.location', 'Warehouse', select=True)
    inventory = fields.Many2One('hrp_inventory.inventory_two', 'Inventory_details', required=False, ondelete='CASCADE')
    lines = fields.Integer('Line', select=True, readonly=True)
    product = fields.Many2One('product.product', 'Product', help='Drugs in code')
    code = fields.Char('Code', readonly=True)
    name = fields.Char('Name', readonly=True)
    uom = fields.Many2One('product.uom', 'Default UOM', required=False, readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    warehouse_num = fields.Float('Warehouse Num', readonly=True)
    freeze_num = fields.Float('Freeze Num', readonly=True)
    warehouse_real_num = fields.Float('Warehouse Real Num', )
    freeze_real_num = fields.Float('Freeze Real Num', )
    scanning = fields.Float('Scanning')
    medicine_machine = fields.Float('medicine_machine')
    cost_pice = fields.Numeric('Cost Price', digits=(16, 2), readonly=True)
    wholesale_amount = fields.Numeric('Wholesale amount', readonly=True, digits=(16, 2))
    references_to = fields.Float('References to', readonly=True)
    lot_warehouse = fields.Many2One('stock.lot', 'Lot Warehouse', context={'locations': [Eval('warehouse')]},
                                    depends=['product', 'warehouse'])
    lot_freeze = fields.Many2One('stock.lot', 'Lot Freeze', context={'locations': [Eval('freeze_warehouse')]})
    differences_why = fields.Selection([('00', u''), ('01', u'少发'), ('02', u'科室结余'), ('03', u'半片医嘱'),
                                        ('04', u'发混'), ('05', u'盘点偏差'), ('06', u'原因不明，重点监控'), ('07', u'相似药品差错'),
                                        ('08', u'患者遗漏'), ('09', u'患者未取药，电脑误确'), ('10', u'多发'),
                                        ('11', u'发药未及时确认')], 'Differences Why', required=False)
    category = fields.Many2One('product.category', 'Category', select=True, required=True)
    type = fields.Selection([
        ('surplus', u'盘盈'),
        ('shortages', u'盘亏'),
        ('balance', u'平衡')
    ], 'Type', readonly=True)
    note = fields.Char('Note')
    difference = fields.Float('Difference')
    state = fields.Selection([('draft', u'起草'), ('done', u'完成'), ('processing', u'处理中')], 'State', required=False)

    @staticmethod
    def default_state():
        return 'draft'

    @fields.depends('warehouse_num', 'warehouse_real_num', 'freeze_real_num', 'lot_warehouse', 'references_to',
                    'product', 'inventory')
    def on_change_warehouse_real_num(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        lists = []
        Lot = Pool().get('stock.lot')
        try:
            self.references_to = self.warehouse_real_num + self.freeze_real_num
        except TypeError:
            self.references_to = self.warehouse_real_num
        if self.warehouse_num < self.warehouse_real_num:
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([self.inventory.warehouse.storage_location.id],
                                                               [self.product.id], with_childs=True,
                                                               grouping=('product', 'lot'))
                # key = warehouse_quant.keys()
                for key, value in warehouse_quant.items():
                    if value != 0.0:
                        if key[-1] != None:
                            lists.append(key[-1])
                lot_list = []
                if lists != []:
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
                    self.lot_warehouse = lots_list[0]
                    self.differences_why = '01'
                else:
                    pass
        elif self.warehouse_num > self.warehouse_real_num:
            self.differences_why = '01'
        else:
            pass

    @fields.depends('freeze_num', 'freeze_real_num', 'lot_freeze', 'references_to', 'warehouse_real_num', 'product',
                    'inventory')
    def on_change_freeze_real_num(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        freeze_id = config.return_of.id
        lists = []
        Lot = Pool().get('stock.lot')
        try:
            self.references_to = self.warehouse_real_num + self.freeze_real_num
        except TypeError:
            self.references_to = self.freeze_real_num
        if self.freeze_num < self.freeze_real_num and self.freeze_num != 0:
            sdsdd = self.inventory
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quant = Product.products_by_location([freeze_id], [self.product.id], with_childs=True,
                                                               grouping=('product', 'lot'))
                for key, value in warehouse_quant.items():
                    if value != 0.0:
                        if key[-1] != None:
                            lists.append(key[-1])
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
            self.lot_freeze = lots_list[0]
        elif self.freeze_num > self.freeze_real_num:
            self.differences_why = '01'
        else:
            pass


class ModifyThe(ModelView):
    "Modify The"
    __name__ = "modify_the"
    inventory = fields.Many2One('hrp_inventory.inventory_two', 'InventoryTwo', select=True)
    warehouse = fields.Many2One('stock.location', 'Warehouse', select=True)
    warehouse_freeze = fields.Many2One('stock.location', 'warehouse_freeze', select=True)
    product = fields.Many2One('product.product', 'Product', help='Drugs in code', domain=[
        ('id', 'in', Eval('products'))], depends=['products'])
    products = fields.Function(fields.One2Many('product.product', None, 'Products'), 'on_change_with_products')
    uom = fields.Many2One('product.uom', 'Default UOM', required=False, readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    warehouse_real_num = fields.Float('Warehouse Real Num', )
    freeze_real_num = fields.Float('Freeze Real Num', )
    lots = fields.Function(fields.One2Many('stock.lot', None, 'Lots'), 'on_change_with_lots')
    lot_warehouse = fields.Many2One('stock.lot', 'Lot Warehouse',
                                    domain=[('product', '=', Eval('product')), ],#('id', 'in', Eval('lots'))
                                    context={'locations': [Eval('warehouse')]},
                                    depends=['product', 'warehouse', 'inventory', 'lots'])
    lot_freezes = fields.Function(fields.One2Many('stock.lot', None, 'lot_freezes'), 'on_change_with_lot_freezes')
    lot_freeze = fields.Many2One('stock.lot', 'Lot Freeze', context={
        'locations': [Eval('warehouse_freeze')]}, domain=[('product', '=', Eval('product')),],#('id', 'in', Eval('lot_freezes'))
                                 depends=['product', 'warehouse_freeze', 'lot_freezes'])
    dom = fields.Date('DOM', readonly=True)
    balance_why = fields.Selection([('00', u'')], 'Balance Why', required=False, states={
        'invisible': Not(Equal(Eval('type'), 'balance')),
    })
    surplus_why = fields.Selection([('00', u''), ('01', u'少发'), ('02', u'科室结余'), ('03', u'半片医嘱'),
                                    ('04', u'发混'), ('05', u'盘点偏差'), ('06', u'原因不明，重点监控'), ('07', u'相似药品差错'),
                                    ('08', u'患者遗漏'), ('09', u'患者未取药，电脑误确')], 'Surplus Why', required=False, states={
        'invisible': Not(Equal(Eval('type'), 'surplus'))
    })
    shortages_why = fields.Selection([('00', u''), ('10', u'多发'), ('02', u'科室结余'),
                                      ('06', u'原因不明，重点监控'), ('05', u'盘点偏差'),
                                      ('11', u'发药未及时确认'), ('07', u'相似药品差错'), ('04', u'发混')], 'Shortages Why',
                                     required=False, states={
            'invisible': Not(Equal(Eval('type'), 'shortages')),
        })
    note = fields.Char('Note')
    line = fields.One2Many('modify_the_inventory_lines', None, 'line', readonly=False)
    confirm = fields.Boolean('Confirm')
    type = fields.Selection([
        ('0', ''),
        ('surplus', u'盘盈'),
        ('shortages', u'盘亏'),
        ('balance', u'平衡')
    ], 'Type', readonly=True)

    @staticmethod
    def default_type():
        return '00'

    @staticmethod
    def default_warehouse():
        InventoryTwoLines = Pool().get('hrp_inventory.inventory_two')
        inventory_two = InventoryTwoLines.search([('id', '=', Transaction().context.get('active_id'))])
        warehouse = inventory_two[0].warehouse.id
        return warehouse

    @staticmethod
    def default_warehouse_freeze():
        InventoryTwoLines = Pool().get('hrp_inventory.inventory_two')
        inventory_two = InventoryTwoLines.search([('id', '=', Transaction().context.get('active_id'))])
        warehouse = inventory_two[0].warehouse.freeze_location.id
        return warehouse

    @staticmethod
    def default_inventory():
        return Transaction().context.get('active_id')

    @fields.depends('warehouse_freeze', 'product')
    def on_change_with_lot_freezes(self, name=None):
        if self.warehouse_freeze and self.product:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.warehouse_freeze.id], [self.product.id], with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value > 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('warehouse', 'product')
    def on_change_with_lots(self, name=None):
        if self.warehouse and self.product:
            Date = Pool().get('ir.date')
            Product = Pool().get('product.product')
            with Transaction().set_context(stock_date_end=Date.today()):
                pbl = Product.products_by_location([self.warehouse.id], [self.product.id], with_childs=True,
                                                   grouping=('product', 'lot'))
                hrp_quantity = []
                for key, value in pbl.items():
                    if value > 0 and key[2] != None:
                        hrp_quantity.append(key[2])
                return hrp_quantity

    @fields.depends('inventory')
    def on_change_with_products(self, name=None):
        # Config = Pool().get('purchase.configuration')
        # config = Config(1)
        # warehouse = config.warehouse.id
        Product = Pool().get('product.product')
        InventoryTwo = Pool().get('hrp_inventory.inventory_two')
        products = Product.search([])
        # OrderPoint = Pool().get('stock.order_point')
        # Inventory_details = InventoryTwo(self.inventory).Inventory_details
        # if InventoryTwo(self.inventory).warehouse.id == warehouse:
        #     order_point = OrderPoint.search([('warehouse_location','=',InventoryTwo(self.inventory).warehouse.id),
        #                    ('type','=','purchase')])
        # else:
        #     order_point = OrderPoint.search([('secondary','=',InventoryTwo(self.inventory).warehouse.id),
        #                    ('type','=','internal')])
        lines = []
        for product in products:
            if InventoryTwo(self.inventory).categories_two != u'全部':
                category_all = InventoryTwo(self.inventory).categories_two
            else:
                category_all = [u'西药', u'中成药']
            if product.template.categories[0].name in category_all:
                lines.append(product.id)
        return lines

    @fields.depends('freeze_num', 'warehouse_num', 'uom', 'freeze_real_num', 'lot_freeze', 'warehouse_real_num', 'note',
                    'product', 'confirm', 'lot_warehouse', 'warehouse', 'drug_specifications',
                    'inventory', 'type', 'shortages_why', 'surplus_why', 'warehouse_freeze')
    def on_change_confirm(self, name=None):
        if self.product and self.confirm:
            Product = Pool().get('product.product')
            Date = Pool().get('ir.date')
            InventoryTwo = Pool().get("hrp_inventory.inventory_two")
            Inventory_details = InventoryTwo(self.inventory).Inventory_details
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    warehouse_real_num = line.warehouse_real_num
                    freeze_real_num = line.freeze_real_num
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([self.warehouse.id], [self.product.id],
                                                                       with_childs=True, grouping=('product', 'lot'))
                        freeze_quant = Product.products_by_location([self.warehouse_freeze.id], [self.product.id],
                                                                       with_childs=True, grouping=('product', 'lot'))
                    if self.lot_warehouse:
                        if warehouse_real_num - self.warehouse_real_num > warehouse_quant[(
                                self.warehouse.id, self.product.id,
                                self.lot_warehouse.id)] and warehouse_real_num - self.warehouse_real_num > 0:
                            self.raise_user_error(u'该批次数量不符合要求')
                    if self.lot_freeze:
                        if freeze_real_num - self.freeze_real_num > freeze_quant[(
                                self.warehouse_freeze.id, self.product.id,
                                self.lot_freeze.id)] and freeze_real_num - self.freeze_real_num > 0:
                            self.raise_user_error(u'该批次数量不符合要求')
            line_list = []
            line_dict = {}
            if self.type == 'surplus':
                differences_why = self.surplus_why
            elif self.type == 'shortages':
                differences_why = self.shortages_why
            else:
                differences_why = u'00'
            line_dict['product'] = self.product
            line_dict['uom'] = self.uom
            line_dict['drug_specifications'] = self.drug_specifications
            line_dict['warehouse_num'] = self.warehouse_num
            line_dict['freeze_num'] = self.freeze_num
            line_dict['warehouse_real_num'] = self.warehouse_real_num
            line_dict['freeze_real_num'] = self.freeze_real_num
            line_dict['lot_warehouse'] = self.lot_warehouse
            line_dict['lot_freeze'] = self.lot_freeze
            line_dict['differences_why'] = differences_why
            line_dict['type'] = self.type
            line_dict['note'] = self.note
            aDay = timedelta(days=0)
            if self.lot_freeze and self.lot_warehouse:
                if self.lot_freeze.date_of_production - self.lot_warehouse.date_of_production > aDay:
                    line_dict['dom'] = self.lot_freeze.date_of_production
                line_dict['dom'] = self.lot_warehouse.date_of_production
                # try:
                #     line_dict['dom'] = self.lot_warehouse.date_of_production
                # except:
                #     line_dict['dom'] = self.lot_freeze.date_of_production
            line_list.append(line_dict)
            self.line = line_list
            self.product = None
            self.uom = None
            self.warehouse_num = None
            self.freeze_num = None
            self.warehouse_real_num = None
            self.freeze_real_num = None
            self.lot_warehouse = None
            self.lot_freeze = None
            self.note = None
            self.confirm = False
            self.drug_specifications = ''

    @fields.depends('freeze_num', 'warehouse_num', 'uom', 'freeze_real_num', 'lot_freeze', 'warehouse_real_num',
                    'product',
                    'lot_warehouse', 'warehouse', 'inventory')
    def on_change_product(self, name=None):
        if self.product:
            InventoryTwo = Pool().get("hrp_inventory.inventory_two")
            Inventory_details = InventoryTwo(self.inventory).Inventory_details
            is_true = True
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    self.drug_specifications = line.drug_specifications
                    self.uom = line.uom.id
                    self.warehouse_real_num = line.warehouse_real_num
                    self.freeze_real_num = line.freeze_real_num
                    is_true = False
                    break
            if is_true:
                self.drug_specifications = self.product.template.drug_specifications
                self.uom = self.product.template.default_uom.id
                self.warehouse_real_num = 0
                self.freeze_real_num = 0
        else:
            self.product = None
            self.uom = None
            self.warehouse_num = None
            self.freeze_num = None
            self.warehouse_real_num = None
            self.freeze_real_num = None
            self.lot_warehouse = None
            self.lot_freeze = None

            self.note = None
            self.confirm = False
            self.drug_specifications = None

    @fields.depends('warehouse_num', 'warehouse_real_num', 'freeze_real_num', 'lot_warehouse', 'product', 'warehouse',
                    'uom', 'inventory')
    def on_change_lot_warehouse(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        InventoryTwo = Pool().get("hrp_inventory.inventory_two")
        Inventory_details = InventoryTwo(self.inventory).Inventory_details
        if self.lot_warehouse and self.warehouse and self.product:
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    warehouse_real_num = line.warehouse_real_num
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([self.warehouse.id], [self.product.id],
                                                                       with_childs=True, grouping=('product', 'lot'))
                    if warehouse_real_num - self.warehouse_real_num > warehouse_quant[(
                            self.warehouse.id, self.product.id,
                            self.lot_warehouse.id)] and warehouse_real_num - self.warehouse_real_num > 0:
                        self.raise_user_error(u'该批次数量不符合要求')
        for line in Inventory_details:
            if line.product.id == self.product.id:
                if self.freeze_real_num + self.warehouse_real_num > line.references_to:
                    self.type = 'surplus'
                elif self.freeze_real_num + self.warehouse_real_num < line.references_to:
                    self.type = 'shortages'
                else:
                    self.type = 'balance'

    @fields.depends('warehouse_num', 'warehouse_real_num', 'freeze_real_num', 'lot_freeze', 'product', 'warehouse_freeze',
                    'uom', 'inventory')
    def on_change_lot_freeze(self, name=None):
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        InventoryTwo = Pool().get("hrp_inventory.inventory_two")
        Inventory_details = InventoryTwo(self.inventory).Inventory_details
        if self.lot_freeze and self.warehouse_freeze and self.product:
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    freeze_real_num = line.freeze_real_num
                    with Transaction().set_context(stock_date_end=Date.today(), stock_assign=True):  # 查看具体库下面的批次对应的数量
                        warehouse_quant = Product.products_by_location([self.warehouse_freeze.id], [self.product.id],
                                                                       with_childs=True, grouping=('product', 'lot'))
                    if freeze_real_num - self.freeze_real_num > warehouse_quant[(
                            self.warehouse_freeze.id, self.product.id,
                            self.lot_freeze.id)] and freeze_real_num - self.freeze_real_num > 0:
                        self.raise_user_error(u'该批次数量不符合要求')
        for line in Inventory_details:
            if line.product.id == self.product.id:
                if self.freeze_real_num + self.warehouse_real_num > line.references_to:
                    self.type = 'surplus'
                elif self.freeze_real_num + self.warehouse_real_num < line.references_to:
                    self.type = 'shortages'
                else:
                    self.type = 'balance'

    @fields.depends('warehouse_num', 'warehouse_real_num', 'freeze_real_num', 'lot_warehouse', 'product', 'warehouse',
                    'uom', 'type', 'inventory')
    def on_change_warehouse_real_num(self, name=None):
        Uom = Pool().get('product.uom')
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        lists = []
        Lot = Pool().get('stock.lot')
        InventoryTwo = Pool().get("hrp_inventory.inventory_two")
        Inventory_details = InventoryTwo(self.inventory).Inventory_details
        with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
            warehouse_quants = Product.products_by_location([self.warehouse.id], [self.product.id], with_childs=True)
            warehouse_quant = Product.products_by_location([self.warehouse.id], [self.product.id], with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if key[-1] != None:
                    lists.append(key[-1])
            lot_list = []
            if lists != []:
                for lot_id in lists:
                    search_lot = Lot.search([
                        ('id', '=', lot_id),
                        ('shelf_life_expiration_date', '>', Date.today())
                    ])
                    for lot in search_lot:
                        dict_sorted = {}
                        expiraton = lot.shelf_life_expiration_date
                        dict_sorted['id'] = lot_id
                        dict_sorted['time_stamp'] = str(expiraton)
                        lot_list.append(dict_sorted)
                if not lot_list:
                    self.raise_user_error(u'请创建该批次')
                lots_list = sorted(lot_list, key=operator.itemgetter('time_stamp'))
            if self.warehouse_real_num > Uom.compute_qty(self.product.default_uom,
                                                         warehouse_quants[(self.warehouse.id, self.product.id)],
                                                         self.uom):
                self.lot_warehouse = lots_list[0]
            else:
                self.lot_warehouse = None
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    if self.freeze_real_num + self.warehouse_real_num > line.references_to:
                        self.type = 'surplus'
                    elif self.freeze_real_num + self.warehouse_real_num < line.references_to:
                        self.type = 'shortages'
                    else:
                        self.type = 'balance'

    @fields.depends('freeze_num', 'freeze_real_num', 'lot_freeze', 'warehouse_real_num', 'product', 'warehouse', 'uom',
                    'type', 'inventory')
    def on_change_freeze_real_num(self, name=None):
        Uom = Pool().get('product.uom')
        Product = Pool().get('product.product')
        Date = Pool().get('ir.date')
        lists = []
        Lot = Pool().get('stock.lot')
        InventoryTwo = Pool().get("hrp_inventory.inventory_two")
        Inventory_details = InventoryTwo(self.inventory).Inventory_details
        with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
            warehouse_quants = Product.products_by_location([self.warehouse.freeze_location.id], [self.product.id],
                                                            with_childs=True)
            warehouse_quant = Product.products_by_location([self.warehouse.freeze_location.id], [self.product.id],
                                                           with_childs=True,
                                                           grouping=('product', 'lot'))
            for key, value in warehouse_quant.items():
                if key[-1] != None:
                    lists.append(key[-1])
            lot_list = []
            for lot_id in lists:
                search_lot = Lot.search([
                    ('id', '=', lot_id), ('shelf_life_expiration_date', '>', Date.today())])
                for lot in search_lot:
                    dict_sorted = {}
                    expiraton = lot.shelf_life_expiration_date
                    dict_sorted['id'] = lot_id
                    dict_sorted['time_stamp'] = str(expiraton)
                    lot_list.append(dict_sorted)
            if not lot_list:
                self.raise_user_error(u'请创建该批次')
            lots_list = sorted(lot_list, key=operator.itemgetter('time_stamp'))
            if self.freeze_real_num > Uom.compute_qty(self.product.default_uom, warehouse_quants[
                (self.warehouse.freeze_location.id, self.product.id)], self.uom):

                self.lot_freeze = lots_list[0]
            else:

                self.lot_freeze = None
            for line in Inventory_details:
                if line.product.id == self.product.id:
                    if self.freeze_real_num + self.warehouse_real_num > line.references_to:
                        self.type = 'surplus'
                    elif self.freeze_real_num + self.warehouse_real_num < line.references_to:
                        self.type = 'shortages'
                    else:
                        self.type = 'balance'


class ModifyTheInventorylines(ModelView):
    "ModifyTheInventorylines"
    __name__ = "modify_the_inventory_lines"

    product = fields.Many2One('product.product', 'Product', help='Drugs in code')
    uom = fields.Many2One('product.uom', 'Default UOM', required=False, readonly=True)
    drug_specifications = fields.Char('Drug Speic', readonly=True)
    warehouse_num = fields.Float('Warehouse Num', readonly=True)
    freeze_num = fields.Float('Freeze Num', readonly=True)
    warehouse_real_num = fields.Float('Warehouse Real Num', )
    freeze_real_num = fields.Float('Freeze Real Num', )
    lot_warehouse = fields.Many2One('stock.lot', 'Lot Warehouse',
                                    domain=[('product', '=', Eval('product')), ('hrp_quantity', '!=', 0)],
                                    context={'locations': [Eval('warehouse')]}, depends=['product', 'warehouse'])
    lot_freeze = fields.Many2One('stock.lot', 'Lot Freeze', context={
        'locations': [Eval('freeze_warehouse')]}, domain=[('product', '=', Eval('product'))],
                                 depends=['product', 'freeze_warehouse'])
    dom = fields.Date('DOM', readonly=True)
    differences_why = fields.Selection([('00', u''), ('01', u'少发'), ('02', u'科室结余'), ('03', u'半片医嘱'),
                                        ('04', u'发混'), ('05', u'盘点偏差'), ('06', u'原因不明，重点监控'), ('07', u'相似药品差错'),
                                        ('08', u'患者遗漏'), ('09', u'患者未取药，电脑误确'), ('10', u'多发'),
                                        ('11', u'发药未及时确认')], 'Differences Why', required=False)
    type = fields.Selection([
        ('0', ''),
        ('surplus', u'盘盈'),
        ('shortages', u'盘亏'),
        ('balance', u'平衡')
    ], 'Type', readonly=True)
    note = fields.Char('Note')


class ModifyTheInventory(Wizard):
    'Modify the inventory'
    __name__ = 'modify_the_inventory'
    start = StateView('modify_the',
                      'hrp_inventory.hrp_inventory_modify_the_view_form', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Create', 'create_', 'tryton-ok'),
                      ])
    create_ = StateAction('hrp_inventory.wizard_modify_the_inventory')

    def do_create_(self, action):
        InventoryTwoLines = Pool().get('hrp_inventory.inventory_two_lines')
        Location = Pool().get('stock.location')
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')
        Date = Pool().get('ir.date')
        data = {}
        for state_name, state in self.states.iteritems():
            if isinstance(state, StateView):
                data[state_name] = getattr(self, state_name)._default_values
        for line in data['start']['line']:
            factor = round((Product(line['product']).default_uom.factor * Uom(line['uom']).rate), 3)  # 单位换算
            with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                warehouse_quants = Product.products_by_location([data['start']['warehouse']], [line['product']],
                                                                with_childs=True)
                warehouse_freeze = Product.products_by_location([data['start']['warehouse_freeze']], [line['product']],
                                                                with_childs=True)
                # if line['warehouse_real_num'] + euwidjfkwio= line['freeze_real_num'] == (warehouse_quants[(data['start']['warehouse'], line['product'])] +warehouse_freeze[(data['start']['warehouse_freeze'], line['product'])]) * factor:
                #     continue
            twolines = InventoryTwoLines.search([
                ('product', '=', line['product']),
                ('inventory', '=', Transaction().context['active_id']),
                ('warehouse', '=', Location(data['start']['warehouse']).storage_location.id)
            ])
            wholesale_amount = decimal.Decimal(str((line['warehouse_real_num'] +
                                                    line['freeze_real_num']) * factor)) * Product(
                line['product']).template.cost_price
            InventoryTwoLines.write(twolines, {'warehouse_real_num': line['warehouse_real_num'],
                                               'references_to': line['warehouse_real_num'] + line['freeze_real_num'],
                                               'wholesale_amount': wholesale_amount.quantize(decimal.Decimal('0.00')),
                                               'type': line['type'],
                                               'freeze_real_num': line['freeze_real_num'],
                                               'differences_why': line['differences_why'],
                                               'lot_warehouse': line['lot_warehouse'],
                                               'lot_freeze': line['lot_freeze'], 'note': line['note']})
