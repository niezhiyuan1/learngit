from trytond.pool import Pool
from .new_product import *
from .price_master_data import *
from .configuration import *


def register():
    Pool.register(
        Configuration,
        PriceData,
        Template,
        Product,
        New_products,
        module='hrp_product', type_='model')
