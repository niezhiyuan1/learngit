#coding:utf-8
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import PoolMeta


class Configuration:
    "Purchase Configuration"
    __metaclass__ = PoolMeta
    __name__ = 'purchase.configuration'

    default_ = fields.Many2One('party.party','Default',domain=[('type_', '=', 'supplier')],readonly=False,required=True)
    warehouse = fields.Many2One(
        'stock.location', "Warehouse",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)
    medical = fields.Many2One(
        'stock.location', "medical",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    endoscopic = fields.Many2One(
        'stock.location', "endoscopic",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    preparation = fields.Many2One(
        'stock.location', "preparation",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    ward = fields.Many2One(
        'stock.location', "ward",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    herbs = fields.Many2One(
        'stock.location', "herbs",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)


    outpatient_freeze = fields.Many2One(
        'stock.location', "Outpatient Freeze",
        domain=[('type', '!=', 'warehouse')],readonly=False,required=True)
    outpatient_service = fields.Many2One(
        'stock.location', "Outpatient service",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    hospital = fields.Many2One(
        'stock.location', "Hospital",
        domain=[('type', '=', 'warehouse')],readonly=False,required=True)

    hospital_freeze = fields.Many2One(
        'stock.location', "Hospital Freeze",
        domain=[('type', '!=', 'warehouse')],readonly=False,required=True)

    default_scrap = fields.Many2One(
        'stock.location', "Default Scrap",
        domain=[('type', '!=', 'warehouse')],readonly=False,required=True) #报废区

    caustic_excessive = fields.Many2One('party.party', "Caustic excessive",readonly=False,required=False)#报损报溢默认供应商

    in_storage = fields.Property(fields.Many2One('ir.sequence',
            'in_storage', required=True))
    loss_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'loss_sequence', required=True))
    overflow_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'overflow_sequence', required=True))
    outpatient_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'outpatient_sequence', required=True))
    hospital_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'hospital_sequence', required=True))
    straight_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'straight_sequence', required=True))
    complete_sequence = fields.Property(fields.Many2One('ir.sequence',
                                                    'complete_sequence', required=True))
    return_of = fields.Many2One(
        'stock.location', "Return of",
        domain=[('type', '!=', 'warehouse')],readonly=False,required=True)
    supplier_payment_term = fields.Many2One('account.invoice.payment_term',required=True, string='Supplier Payment Term')

    transfers = fields.Many2One(
        'stock.location', "Transfers",readonly=False,required=True) #中转库存地
