from .new_purchase_request import *
from trytond.pool import Pool
from .configuration import *
from .invoice import *


def register():
    Pool.register(
        NewCreatePurchaseRequestStart,
        Configuration,
        Invoice,
        Purchase,
        module='hrp_purchase_request', type_='model')
    Pool.register(
        NewCreatePurchaseRequest,
        module='hrp_purchase_request', type_='wizard')
