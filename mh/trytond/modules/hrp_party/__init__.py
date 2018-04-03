from trytond.pool import Pool
from .new_party import  *
from .new_party import *

def register():
    Pool.register(
        New_party,
        Party,
        module='hrp_party', type_='model')