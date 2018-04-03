from trytond.pool import Pool
from .department import  *


def register():
    Pool.register(
        Department,
        module='hrp_department', type_='model')