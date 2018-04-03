from trytond.pool import Pool
from .wms_location import *
def register():
    Pool.register(
        ProductQuantity,
        Interfaceq,
        module='hrp_wms', type_='model')

