from .shipment import *
from trytond.pool import Pool
from .location import *
from .stock_return import *
from .caustic_excessive import *
def register():
    Pool.register(
        OrderNo,
        HrpShipmentLines,
        HrpShipment,
        ShipmentOrder,
        ShipmentOrderLines,
        ZdrugSaleorder,
        ShipmentIn,
        HrpSaleLines,
        HrpSale,
        HrpShipmentReturn,
        HrpShipmentReturnLines,
        Location,
        CausticExcessive,
        CausticExcessiveLines,
        StockReturn,
        StockReturnLines,
        ShipmentInReturn,
        PurchaseBills,
        ShipmentOutReturn,
        AuditCausticExcessiveLines,
        AuditCausticExcessive,
        CausticExcessiveStorage,
        module='hrp_shipment', type_='model')
    Pool.register(
        CreatePurchaseShipment,
        CreateShipmentOrder,
        CausticExcessiveCreate,
        HrpCreateSale,
        CreatePurchaseShipmentReturn,
        CreateStockReturn,
        AuditCausticExcessiveCreate,
        module='hrp_shipment', type_='wizard')
    Pool.register(
        HrpSaleReport,
        module='hrp_shipment', type_='report')

