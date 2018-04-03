from trytond.pool import Pool
from .order_point import *

def register():
    Pool.register(
        OrderPoint,
        PurchaseRreference,
        module='hrp_order_point', type_='model')
