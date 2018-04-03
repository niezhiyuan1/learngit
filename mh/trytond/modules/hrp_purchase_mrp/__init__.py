from .purchase_mrp import *
from trytond.pool import Pool
from .purchase_line import *

def register():
    Pool.register(
        CreatePurchaseMrpStart,
        PurchaseMrpLines,
        PurchaseLine,
        CreatePurchaseAskParty,
        Lot,
        module='hrp_purchase_mrp', type_='model')
    Pool.register(
        CreatePurchaseMrp,
        CreatePurchase,
        module='hrp_purchase_mrp', type_='wizard')

