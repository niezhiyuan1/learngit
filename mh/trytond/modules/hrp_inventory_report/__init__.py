from trytond.pool import Pool
from inventory_report import *


def register():
    Pool.register(
        InventoryReport,
        InventoryReportConditionsStart,
        StockInventoryReportStart,
        StockInventoryReport,
        StockShipmentReportStart,
        StockShipmentCategoryReport,
        StockShipmentInvoiceReport,
        StockShipmentOrderReport,
        StockShipmentOrderInReport,
        module='hrp_inventory_report', type_='model')
    Pool.register(
        InventoryReportConditionsWizard,
        StockInventoryReportWizard,
        StockShipmentReportWizard,
        module='hrp_inventory_report', type_='wizard')
