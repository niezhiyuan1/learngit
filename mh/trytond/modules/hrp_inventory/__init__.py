from .inventory import *
from trytond.pool import Pool
from .available_medicine import *


def register():
    Pool.register(
        Inventory,
        AvailableMedicine,
        AvailableMedicineLine,
        InventoryLines,
        InventoryTwo,
        InventoryTwoLines,
        ModifyThe,
        ModifyTheInventorylines,
        InventoryTime,
        ShelvesName,
        module='hrp_inventory', type_='model')
    Pool.register(
        InventoryReport,
        InventoryTwoReport,
        module='hrp_inventory', type_='report')
    Pool.register(
        ModifyTheInventory,
        module='hrp_inventory', type_='wizard')
