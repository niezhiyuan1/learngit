from trytond.pool import Pool
from hrp_new_product import *
from hrp_product_condition import *
from hrp_new_return import *
from hrp_return_request import *

def register():
    Pool.register(
        NewProduct,
        ProductCondition,
        NewReturn,
        InternalReturnRequest,
        TestlReturnRequest,
        module='hrp_new_product', type_='model')
    Pool.register(
        ProductConditionWizard,
        InternalReturnRequestWizard,
        module='hrp_new_product', type_='wizard')