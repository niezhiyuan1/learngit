# coding:utf-8
import decimal
import operator
from trytond.modules.product import Uom
from trytond.pool import Pool
from trytond.model import fields, ModelView, Workflow
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction

__all__ = ['ShipmentInternal']


class Overlay(object):
    pass


class Position(object):
    pass


class ShipmentInternal:
    __metaclass__ = PoolMeta

    __name__ = "stock.shipment.internal"

    drug_starts = fields.Selection([
        ('00', u'西药'),
        ('01', u'中成药'),
        ('02', u'中草药'),
        ('03', u'颗粒中'),
        ('04', u'原料药'),
        ('05', u'敷药'),
        ('06', u''),
        ('07', u'同位素'),
    ], 'drug_starts', select=True)  # 药品类型

    starts = fields.Selection([
        ('00', u'常规药品请领单'),
        ('01', u'请退单'),
        ('02', u'非限制转冻结'),
        ('03', u'冻结转非限制'),
        ('04', u'内部调拨'),
        ('06', u'直送药品请领单'),
        ('07', u''),
    ], 'Starts', select=True)  # 移动类型

    straights = fields.Boolean('straights', select=True)
    place_of_service = fields.Many2One('stock.location', 'place_of_service', select=True)
    move_type = fields.Selection([
        ('00', u'type'),
        ('01', u'type1'),
    ], 'Type')
    return_shipment = fields.Many2One('order_no', 'Return Shipment', select=True, readonly=True)  # 采退单号

    @staticmethod
    def default_move_type():
        return '01'

    @staticmethod
    def default_drug_starts():
        return '06'

    @staticmethod
    def default_starts():
        return '07'

    @staticmethod
    def default_examine():
        return '03'

    @classmethod
    @ModelView.button
    @Workflow.transition('waiting')
    def wait(cls, shipments):
        Config = Pool().get('purchase.configuration')
        config = Config(1)  # 库存地配置
        Lot = Pool().get('stock.lot')
        Move = Pool().get('stock.move')
        Move.draft([m for s in shipments for m in s.moves])
        internal = Pool().get('stock.shipment.internal')
        Product = Pool().get('product.product')
        ProductQuantity = Pool().get('product_quantity')
        Date = Pool().get('ir.date')
        today = str(Date.today())
        moves = []
        lv = {}
        list = []
        lists_lots = []
        writelist = []
        lot_dele_list = []
        dicts = {}
        # 通过有限期进行排序的id

        for shipment in shipments:
            order_number = shipment.number
            internal_id = shipment.id
            to_location = shipment.to_location
            from_location = shipment.from_location
            place_of_service = shipment.place_of_service
            starts = shipment.starts
            company = shipment.company
            drug_starts = shipment.drug_starts
            lv['state'] = u'draft'
            lv['starts'] = starts
            lv['to_location'] = to_location
            lv['from_location'] = from_location
            lv['company'] = company
            move_all_id = []
            waite_move_id = []
            for move in shipment.moves:
                move_all_id.append(move.id)
                if move.state != 'done':
                    moves.append(move)
                if move.outgoing_audit == '03':
                    dict = {}
                    dict['origin'] = None
                    dict['to_location'] = config.transfers.id  # move.to_location中转库
                    dict['product'] = move.product.id
                    dict['from_location'] = move.from_location
                    dict['invoice_lines'] = []
                    dict['company'] = move.company.id
                    if move.is_direct_sending == True:
                        lv['straights'] = True
                    else:
                        lv['straights'] = False
                    dict['is_direct_sending'] = move.is_direct_sending
                    dict['unit_price'] = move.unit_price
                    dict['lot'] = move.lot
                    dict['uom'] = move.uom
                    dict['starts'] = move.starts
                    dict['real_number'] = move.real_number
                    dict['change_start'] = move.change_start
                    dict['purchase_order'] = move.purchase_order
                    lv['place_of_service'] = place_of_service
                    lv['drug_starts'] = drug_starts
                    dict['quantity'] = move.quantity
                    list.append(dict)
                    lv['number'] = order_number
                    lv['moves'] = [['create', list]]
                    lv['planned_date'] = today
                    lists_lots.append(move.id)
                    waite_move_id.append(move.id)
                elif move.outgoing_audit == '01':
                    dicts['quantity'] = 0
                    writelist.append(move.id)
                elif move.outgoing_audit == '00':
                    if move.lot != None:
                        pass
                    else:
                        if move.from_location.id == config.warehouse.storage_location.id:
                            QuantityPro = ProductQuantity.search(['product', '=', move.product.id],
                                                                 order=[["sequence", "ASC"]])
                            quantity = move.quantity
                            rule_list = []
                            if QuantityPro:
                                for each in QuantityPro:
                                    with Transaction().set_context(stock_date_end=Date.today()):  # 查看具体库下面的批次对应的数量
                                        warehouse_quant = Product.products_by_location([each.location.id],
                                                                                       [move.product.id],
                                                                                       with_childs=True,
                                                                                       grouping=('product', 'lot'))
                                        for key, value in warehouse_quant.items():
                                            if value > 0.0:
                                                if key[-1] != None:
                                                    search_lot = Lot.search(['id', '=', key[-1]])
                                                    rule_message = {}
                                                    rule_message['location'] = each.location.id
                                                    rule_message['sequence'] = each.sequence
                                                    rule_message['product'] = move.product.id
                                                    rule_message['time'] = search_lot[0].shelf_life_expiration_date
                                                    rule_message['number'] = value
                                                    rule_message['lot'] = key[-1]
                                                    rule_list.append(rule_message)
                                with Transaction().set_context(stock_date_end=Date.today(),
                                                               stock_assign=True):  # 查看具体库下面的批次对应的数量
                                    warehouse_quant = Product.products_by_location([move.from_location.id],
                                                                                   [move.product.id]
                                                                                   , with_childs=False,
                                                                                   grouping=('product', 'lot'))
                                    for key, value in warehouse_quant.items():
                                        if value > 0.0:
                                            if key[-1] != None:
                                                search_lot = Lot.search(['id', '=', key[-1]])
                                                rule_message = {}
                                                rule_message['location'] = move.from_location.id
                                                rule_message['sequence'] = 1
                                                rule_message['product'] = move.product.id
                                                rule_message['time'] = search_lot[0].shelf_life_expiration_date
                                                rule_message['number'] = value
                                                rule_message['lot'] = key[-1]
                                                rule_list.append(rule_message)
                                Result = sorted(rule_list, key=lambda x: (x['time'], x['sequence']), reverse=False)
                                frequency = 0
                                number_all = 0
                                for i in range(len(rule_list)):
                                    if number_all > quantity:
                                        break
                                    else:
                                        number_all += Result[i]['number']
                                        frequency += 1
                                for strip in range(frequency):
                                    if frequency == 1:
                                        cost_prices = decimal.Decimal(str(float(
                                            move.product.template.cost_price * decimal.Decimal(str(move.quantity)))))
                                        cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                        list_prices = decimal.Decimal(str(float(
                                            move.product.template.list_price * decimal.Decimal(str(move.quantity)))))
                                        list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                        move_dict = {
                                            'comment': '',
                                            'outgoing_audit': '00',
                                            'to_location': config.warehouse.storage_location.id,
                                            'product': move.product.id,
                                            'invoice_lines': [],
                                            'starts': '05',
                                            'move_type': '000',
                                            'company': Transaction().context.get('company'),
                                            'uom': move.uom.id,
                                            'reason': '00',
                                            'planned_date': today,
                                            'change_start': move.change_start,
                                            'purchase_order': move.purchase_order,
                                            'list_price': list_price,
                                            'cost_price': cost_price,
                                        }
                                        if Result[strip]['location'] != config.warehouse.storage_location.id:
                                            move_dict['from_location'] = Result[strip]['location']
                                            move_dict['lot'] = Result[strip]['lot']
                                            move_dict['quantity'] = move.quantity
                                            move_list = Move.create([move_dict])
                                            Move.do(move_list)
                                        else:
                                            pass

                                    else:
                                        cost_prices = decimal.Decimal(str(float(
                                            move.product.template.cost_price * decimal.Decimal(str(move.quantity)))))

                                        cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                        list_prices = decimal.Decimal(str(float(
                                            move.product.template.list_price * decimal.Decimal(str(move.quantity)))))
                                        list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                        if strip == 0:
                                            move_dict = {
                                                'comment': '',
                                                'outgoing_audit': '00',
                                                'to_location': config.warehouse.storage_location.id,
                                                'product': move.product.id,
                                                'invoice_lines': [],
                                                'starts': '05',
                                                'move_type': '000',
                                                'company': Transaction().context.get('company'),
                                                'uom': move.uom.id,
                                                'reason': '00',
                                                'change_start': move.change_start,
                                                'purchase_order': move.purchase_order,
                                                'planned_date': today,
                                                'list_price': list_price,
                                                'cost_price': cost_price,
                                            }
                                            if Result[strip]['location'] != config.warehouse.storage_location.id:
                                                move_dict['from_location'] = Result[strip]['location']
                                                move_dict['lot'] = Result[strip]['lot']
                                                move_dict['quantity'] = Result[strip]['number']
                                                move_list = Move.create([move_dict])
                                                Move.do(move_list)
                                            else:
                                                pass
                                        elif strip == frequency - 1:
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(move.quantity)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(move.quantity)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            move_dict = {
                                                'comment': '',
                                                'outgoing_audit': '00',
                                                'to_location': config.warehouse.storage_location.id,
                                                'product': move.product.id,
                                                'invoice_lines': [],
                                                'starts': '05',
                                                'move_type': '000',
                                                'company': Transaction().context.get('company'),
                                                'uom': move.uom.id,
                                                'reason': '00',
                                                'change_start': move.change_start,
                                                'purchase_order': move.purchase_order,
                                                'planned_date': today,
                                                'cost_price': cost_price,
                                                'list_price': list_price,
                                            }
                                            if Result[strip]['location'] != config.warehouse.storage_location.id:
                                                move_dict['from_location'] = Result[strip]['location']
                                                move_dict['lot'] = Result[strip]['lot']
                                                move_dict['quantity'] = Result[strip][
                                                                            'number'] + move.quantity - number_all
                                                move_list = Move.create([move_dict])
                                                Move.do(move_list)

                                        else:
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(move.quantity)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(move.quantity)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            move_dict = {
                                                'comment': '',
                                                'outgoing_audit': '00',
                                                'to_location': config.warehouse.storage_location.id,
                                                'product': move.product.id,
                                                'invoice_lines': [],
                                                'starts': '05',
                                                'move_type': '000',
                                                'company': Transaction().context.get('company'),
                                                'uom': move.uom.id,
                                                'change_start': move.change_start,
                                                'purchase_order': move.purchase_order,
                                                'reason': '00',
                                                'planned_date': today,
                                                'list_price': list_price,
                                                'cost_price': cost_price,
                                            }
                                            if Result[strip]['location'] != config.warehouse.storage_location.id:
                                                move_dict['from_location'] = Result[strip]['location']
                                                move_dict['lot'] = Result[strip]['lot']
                                                move_dict['quantity'] = Result[strip]['number']
                                                move_list = Move.create([move_dict])
                                                Move.do(move_list)
                                            else:
                                                pass

                            else:
                                pass
                            quantity = move.quantity
                            with Transaction().set_context(stock_date_end=Date.today(),
                                                           stock_assign=True):  # 查看具体库下面的批次对应的数量
                                warehouse_quant = Product.products_by_location([move.from_location.id],
                                                                               [move.product.id],
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
                                for id_lot in range(len_lot):
                                    lot_quant = warehouse_quant[(
                                        move.from_location.id, move.product.id, done_list[id_lot])]  # 对应批次的库存数量
                                    if number >= quantity:
                                        break
                                    else:
                                        num += 1
                                        number += lot_quant
                                for lo in range(num):
                                    cost_prices = decimal.Decimal(str(float(
                                        move.product.template.cost_price * decimal.Decimal(
                                            str(move.quantity)))))
                                    cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                    list_prices = decimal.Decimal(str(float(
                                        move.product.template.list_price * decimal.Decimal(
                                            str(move.quantity)))))
                                    list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                    if num == 1:
                                        lotdict = {}
                                        lotdict['quantity'] = quantity
                                        lotdict['lot'] = done_list[lo]
                                        lotdict['cost_price'] = cost_price
                                        lotdict['list_price'] = list_price
                                        lot_write = Move.search([('id', '=', move.id)])
                                        Move.write(lot_write, lotdict)
                                    else:
                                        if lo == 0:

                                            lot_quant_one = warehouse_quant[
                                                (move.from_location.id, move.product.id, done_list[lo])]
                                            lot_dict = {}
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(lot_quant_one)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(lot_quant_one)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            lot_dict['lot'] = done_list[lo]
                                            lot_dict['quantity'] = lot_quant_one
                                            lot_dict['cost_price'] = cost_price
                                            lot_dict['list_price'] = list_price
                                            lot_write = Move.search([('id', '=', move.id)])
                                            Move.write(lot_write, lot_dict)
                                        elif lo == num - 1:
                                            lots_dicts = {}
                                            shipment = 'stock.shipment.internal,' + str(internal_id)
                                            lot_quant_two = warehouse_quant[
                                                (move.from_location.id, move.product.id, done_list[lo])]
                                            Quantity = lot_quant_two - (number - quantity)
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(Quantity)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(Quantity)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            lots_dicts['outgoing_audit'] = u'00'
                                            lots_dicts['origin'] = None
                                            lots_dicts['to_location'] = move.to_location.id
                                            lots_dicts['shipment'] = shipment
                                            lots_dicts['product'] = move.product.id
                                            lots_dicts['from_location'] = move.from_location.id
                                            lots_dicts['invoice_lines'] = []
                                            lots_dicts['company'] = move.company.id
                                            lots_dicts['is_direct_sending'] = move.is_direct_sending
                                            lots_dicts['unit_price'] = move.unit_price
                                            lots_dicts['lot'] = done_list[lo]
                                            lots_dicts['uom'] = move.uom.id
                                            lots_dicts['starts'] = move.starts
                                            lots_dicts['currency'] = 54
                                            lots_dicts['quantity'] = Quantity
                                            lots_dicts['change_start'] = move.change_start
                                            lots_dicts['purchase_order'] = move.purchase_order
                                            lots_dicts['list_price'] = list_price
                                            lots_dicts['cost_price'] = cost_price
                                            Move.create([lots_dicts])
                                        else:
                                            lot_quant_three = warehouse_quant[
                                                (move.from_location.id, move.product.id, done_list[lo])]
                                            lots_dict = {}
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(lot_quant_three)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(lot_quant_three)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            shipment = 'stock.shipment.internal,' + str(internal_id)
                                            lots_dict['outgoing_audit'] = u'00'
                                            lots_dict['origin'] = None
                                            lots_dict['to_location'] = move.to_location.id
                                            lots_dict['shipment'] = shipment
                                            lots_dict['product'] = move.product.id
                                            lots_dict['from_location'] = move.from_location.id
                                            lots_dict['invoice_lines'] = []
                                            lots_dict['company'] = move.company.id
                                            lots_dict['is_direct_sending'] = move.is_direct_sending
                                            lots_dict['unit_price'] = move.unit_price
                                            lots_dict['lot'] = done_list[lo]
                                            lots_dict['uom'] = move.uom.id
                                            lots_dict['starts'] = move.starts
                                            lots_dict['currency'] = 54
                                            lots_dict['quantity'] = lot_quant_three
                                            lots_dict['change_start'] = move.change_start
                                            lots_dict['purchase_order'] = move.purchase_order
                                            lots_dict['list_price'] = list_price
                                            lots_dict['cost_price'] = cost_price
                                            Move.create([lots_dict])
                        else:
                            min_Package = move.product.min_Package.id
                            uom_id = move.uom.id
                            if min_Package == uom_id:
                                quantity = move.quantity
                                # quantity = Uom.compute_qty(move.product.default_uom, move.quantity,move.product.min_Package, round=True)
                                with Transaction().set_context(stock_date_end=Date.today(),
                                                               stock_assign=True):  # 查看具体库下面的批次对应的数量
                                    warehouse_quant = Product.products_by_location([move.from_location.id],
                                                                                   [move.product.id], with_childs=False,
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
                                    for id_lot in range(len_lot):
                                        lot_quants = warehouse_quant[
                                            (move.from_location.id, move.product.id, done_list[id_lot])]  # 对应批次的库存数量
                                        lot_quant = Uom.compute_qty(move.product.default_uom, lot_quants,
                                                                    move.product.min_Package, round=True)
                                        if number >= quantity:
                                            break
                                        else:
                                            num += 1
                                            number += lot_quant
                                    for lo in range(num):
                                        if num == 1:
                                            lotdict = {}
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(quantity)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(quantity)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            lotdict['quantity'] = quantity
                                            lotdict['lot'] = done_list[lo]
                                            lotdict['list_price'] = list_price
                                            lotdict['cost_price'] = cost_price
                                            lot_write = Move.search([('id', '=', move.id)])
                                            Move.write(lot_write, lotdict)
                                        else:
                                            if lo == 0:
                                                lot_quant_one_ = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                lot_quant_one = Uom.compute_qty(move.product.default_uom,
                                                                                lot_quant_one_,
                                                                                move.product.min_Package, round=True)
                                                lot_dict = {}
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(lot_quant_one)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(lot_quant_one)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                lot_dict['lot'] = done_list[lo]
                                                lot_dict['quantity'] = lot_quant_one
                                                lot_dict['list_price'] = list_price
                                                lot_dict['cost_price'] = cost_price
                                                lot_write = Move.search([('id', '=', move.id)])
                                                Move.write(lot_write, lot_dict)
                                            elif lo == num - 1:
                                                lots_dicts = {}

                                                shipment = 'stock.shipment.internal,' + str(internal_id)
                                                lot_quant_two_ = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                lot_quant_two = Uom.compute_qty(move.product.default_uom,
                                                                                lot_quant_two_,
                                                                                move.product.min_Package, round=True)
                                                Quantity = lot_quant_two - (number - quantity)
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(Quantity)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(Quantity)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                lots_dicts['outgoing_audit'] = u'00'
                                                lots_dicts['origin'] = None
                                                lots_dicts['to_location'] = move.to_location.id
                                                lots_dicts['shipment'] = shipment
                                                lots_dicts['product'] = move.product.id
                                                lots_dicts['from_location'] = move.from_location.id
                                                lots_dicts['invoice_lines'] = []
                                                lots_dicts['company'] = move.company.id
                                                lots_dicts['is_direct_sending'] = move.is_direct_sending
                                                lots_dicts['unit_price'] = move.unit_price
                                                lots_dicts['lot'] = done_list[lo]
                                                lots_dicts['uom'] = move.uom.id
                                                lots_dicts['starts'] = move.starts
                                                lots_dicts['currency'] = 54
                                                lots_dicts['quantity'] = Quantity
                                                lots_dicts['change_start'] = move.change_start
                                                lots_dicts['purchase_order'] = move.purchase_order
                                                lots_dicts['list_price'] = list_price
                                                lots_dicts['cost_price'] = cost_price
                                                Move.create([lots_dicts])
                                            else:
                                                lot_quant_three_ = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                lot_quant_three = Uom.compute_qty(move.product.default_uom,
                                                                                  lot_quant_three_,
                                                                                  move.product.min_Package, round=True)
                                                lots_dict = {}
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(lot_quant_three)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(lot_quant_three)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                shipment = 'stock.shipment.internal,' + str(internal_id)
                                                lots_dict['outgoing_audit'] = u'00'
                                                lots_dict['origin'] = None
                                                lots_dict['to_location'] = move.to_location.id
                                                lots_dict['shipment'] = shipment
                                                lots_dict['product'] = move.product.id
                                                lots_dict['from_location'] = move.from_location.id
                                                lots_dict['invoice_lines'] = []
                                                lots_dict['company'] = move.company.id
                                                lots_dict['is_direct_sending'] = move.is_direct_sending
                                                lots_dict['unit_price'] = move.unit_price
                                                lots_dict['lot'] = done_list[lo]
                                                lots_dict['uom'] = move.uom.id
                                                lots_dict['starts'] = move.starts
                                                # lots_dict['currency'] = 54
                                                lots_dict['quantity'] = lot_quant_three
                                                lots_dict['change_start'] = move.change_start
                                                lots_dict['purchase_order'] = move.purchase_order
                                                lots_dict['list_price'] = list_price
                                                lots_dict['cost_price'] = cost_price
                                                Move.create([lots_dict])
                            else:
                                quantity = move.quantity
                                with Transaction().set_context(stock_date_end=Date.today(),
                                                               stock_assign=True):  # 查看具体库下面的批次对应的数量
                                    warehouse_quant = Product.products_by_location([move.from_location.id],
                                                                                   [move.product.id], with_childs=False,
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
                                    for id_lot in range(len_lot):
                                        lot_quant = warehouse_quant[
                                            (move.from_location.id, move.product.id, done_list[id_lot])]  # 对应批次的库存数量
                                        if number >= quantity:
                                            break
                                        else:
                                            num += 1
                                            number += lot_quant
                                    for lo in range(num):
                                        if num == 1:
                                            lotdict = {}
                                            cost_prices = decimal.Decimal(str(float(
                                                move.product.template.cost_price * decimal.Decimal(
                                                    str(quantity)))))
                                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))

                                            list_prices = decimal.Decimal(str(float(
                                                move.product.template.list_price * decimal.Decimal(
                                                    str(quantity)))))
                                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))

                                            lotdict['quantity'] = quantity
                                            lotdict['lot'] = done_list[lo]
                                            lotdict['list_price'] = list_price
                                            lotdict['cost_price'] = cost_price
                                            lot_write = Move.search([('id', '=', move.id)])
                                            Move.write(lot_write, lotdict)
                                        else:
                                            if lo == 0:
                                                lot_quant_one = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                lot_dict = {}
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(lot_quant_one)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(lot_quant_one)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                lot_dict['lot'] = done_list[lo]
                                                lot_dict['quantity'] = lot_quant_one
                                                lot_dict['list_price'] = list_price
                                                lot_dict['cost_price'] = cost_price
                                                lot_write = Move.search([('id', '=', move.id)])
                                                Move.write(lot_write, lot_dict)
                                            elif lo == num - 1:
                                                lots_dicts = {}

                                                shipment = 'stock.shipment.internal,' + str(internal_id)
                                                lot_quant_two = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                Quantity = lot_quant_two - (number - quantity)
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(Quantity)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(Quantity)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                lots_dicts['outgoing_audit'] = u'00'
                                                lots_dicts['origin'] = None
                                                lots_dicts['to_location'] = move.to_location.id
                                                lots_dicts['shipment'] = shipment
                                                lots_dicts['product'] = move.product.id
                                                lots_dicts['from_location'] = move.from_location.id
                                                lots_dicts['invoice_lines'] = []
                                                lots_dicts['company'] = move.company.id
                                                lots_dicts['is_direct_sending'] = move.is_direct_sending
                                                lots_dicts['unit_price'] = move.unit_price
                                                lots_dicts['lot'] = done_list[lo]
                                                lots_dicts['uom'] = move.uom.id
                                                lots_dicts['starts'] = move.starts
                                                lots_dicts['currency'] = 54
                                                lots_dicts['quantity'] = Quantity
                                                lots_dicts['change_start'] = move.change_start
                                                lots_dicts['purchase_order'] = move.purchase_order
                                                lots_dicts['list_price'] = list_price
                                                lots_dicts['cost_price'] = cost_price
                                                Move.create([lots_dicts])
                                            else:
                                                lot_quant_three = warehouse_quant[
                                                    (move.from_location.id, move.product.id, done_list[lo])]
                                                lots_dict = {}
                                                cost_prices = decimal.Decimal(str(float(
                                                    move.product.template.cost_price * decimal.Decimal(
                                                        str(lot_quant_three)))))
                                                cost_price = decimal.Decimal(cost_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                list_prices = decimal.Decimal(str(float(
                                                    move.product.template.list_price * decimal.Decimal(
                                                        str(lot_quant_three)))))
                                                list_price = decimal.Decimal(list_prices).quantize(
                                                    decimal.Decimal('0.00'))

                                                shipment = 'stock.shipment.internal,' + str(internal_id)
                                                lots_dict['outgoing_audit'] = u'00'
                                                lots_dict['origin'] = None
                                                lots_dict['to_location'] = move.to_location.id
                                                lots_dict['shipment'] = shipment
                                                lots_dict['product'] = move.product.id
                                                lots_dict['from_location'] = move.from_location.id
                                                lots_dict['invoice_lines'] = []
                                                lots_dict['company'] = move.company.id
                                                lots_dict['is_direct_sending'] = move.is_direct_sending
                                                lots_dict['unit_price'] = move.unit_price
                                                lots_dict['lot'] = done_list[lo]
                                                lots_dict['uom'] = move.uom.id
                                                lots_dict['starts'] = move.starts
                                                # lots_dict['currency'] = 54
                                                lots_dict['quantity'] = lot_quant_three
                                                lots_dict['change_start'] = move.change_start
                                                lots_dict['purchase_order'] = move.purchase_order
                                                lots_dict['list_price'] = list_price
                                                lots_dict['cost_price'] = cost_price
                                                Move.create([lots_dict])
        if 'moves' in lv.keys():
            internal.create([lv])
        Move.save(moves)

        for delete_id in lists_lots:
            delete_move = Move.search([('id', '=', delete_id)])
            Move.delete(delete_move)
        for each_ in writelist:
            write_move = Move.search([('id', '=', each_)])
            Move.write(write_move, dicts)
        for delete_lot_id in lot_dele_list:
            delete_move = Move.search([('id', '=', delete_lot_id)])
            Move.delete(delete_move)


        ####################      内部交货完成的创建         ##################

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, shipments):
        pool = Pool()
        Config = Pool().get('purchase.configuration')
        config = Config(1)
        Move = pool.get('stock.move')
        Date = pool.get('ir.date')
        Move.do([m for s in shipments for m in s.moves])
        for i in shipments:
            number_done = i.number
            if number_done[0] == 'Y':
                Number = number_done
            elif number_done[0:2].isalpha() == True:
                Number = number_done

            elif i.starts == '01' and i.to_location.id == config.transfers.id:
                Number = number_done
            else:
                Number = 'Y' + number_done
            cls.write([s for s in shipments if not s.effective_date],
                      {'effective_date': Date.today(), 'number': Number})
        #####################     扩充部分     #######################

        lv = {}
        list = []
        internal = Pool().get('stock.shipment.internal')
        for shipment in shipments:
            starts = shipment.starts
            Number = shipment.number
            straights = shipment.straights
            to_location = shipment.to_location.id
            if to_location == config.transfers.id:  # 中转库id
                place_of_service = shipment.place_of_service.id
                company = shipment.company.id
                drug_starts = shipment.drug_starts
                lv['move_type'] = '00'
                lv['to_location'] = place_of_service
                lv['place_of_service'] = shipment.from_location
                lv['planned_date'] = Date.today()
                lv['from_location'] = config.transfers.id  # 中转库
                lv['company'] = company
                lv['state'] = u'draft'
                lv['number'] = Number
                lv['straights'] = straights
                lv['starts'] = starts
                lv['drug_starts'] = drug_starts
                if shipment.moves == ():
                    pass
                else:
                    for move in shipment.moves:
                        dicts = {}
                        if move.uom == move.product.default_uom:
                            list_prices = decimal.Decimal(
                                str(float(move.product.list_price * decimal.Decimal(str(move.quantity)))))
                            list_price = decimal.Decimal(list_prices).quantize(decimal.Decimal('0.00'))
                            cost_prices = decimal.Decimal(
                                str(float(move.product.cost_price * decimal.Decimal(str(move.quantity)))))  # 零售总价
                            cost_price = decimal.Decimal(cost_prices).quantize(decimal.Decimal('0.00'))
                            dicts['list_price'] = list_price
                            dicts['cost_price'] = cost_price
                        else:
                            cost_prices = Uom.compute_price(move.product.default_uom, move.product.cost_price, move.uom)
                            cost_prices_ = decimal.Decimal(
                                str(float(cost_prices * decimal.Decimal(str(move.quantity)))))  # 零售总价
                            cost_price = decimal.Decimal(cost_prices_).quantize(decimal.Decimal('0.00'))
                            list_prices = Uom.compute_price(move.product.default_uom, move.product.list_price, move.uom)
                            list_prices_ = decimal.Decimal(
                                str(float(list_prices * decimal.Decimal(str(move.quantity)))))  # 批发总价
                            list_price = decimal.Decimal(list_prices_).quantize(decimal.Decimal('0.00'))
                            dicts['list_price'] = list_price
                            dicts['cost_price'] = cost_price

                        dicts['origin'] = None  # each['origin']
                        dicts['to_location'] = place_of_service
                        dicts['product'] = move.product.id
                        dicts['starts'] = move.starts
                        dicts['from_location'] = config.transfers.id  # 中转库
                        dicts['invoice_lines'] = ()  # each['invoice_lines']
                        dicts['company'] = company
                        dicts['is_direct_sending'] = move.is_direct_sending  # 是否直送
                        dicts['reason'] = move.reason  # 请退原因
                        dicts['comment'] = move.comment  # 请退备注
                        if move.lot == None:
                            pass
                        else:
                            dicts['lot'] = move.lot.id
                        dicts['uom'] = move.uom.id
                        dicts['real_number'] = move.real_number  # 产品的请领数量
                        dicts['quantity'] = move.quantity
                        dicts['change_start'] = move.change_start
                        list.append(dicts)
                        lv['moves'] = [['create', list]]
                    internal.create([lv])
            else:
                pass
