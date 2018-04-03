from trytond.pool import Pool
from price_adjustment_report import *
from hrp_price_profit_loss import *
from hrp_stock_report import *
from hrp_expiry_lot_report import *
from hrp_outbound_statistics import *

def register():
    """register"""

    Pool.register(

        HrpReportDisplay,
        HrpStockReport,
        HrpReportCondition,
        PriceAdjustment,
        PriceAdjustmentMessage,
        PriceProfitLoss,
        PriceProfitLossMessage,
        PriceProfitLossContent,
        HrpExpiryLotMessageReport,
        HrpExpiryLotContent,
        HrpOutboundStatisticsReportOne,
        HrpOutboundStatisticsContent,
        HrpOutboundStatisticsReportProduct,
        HrpOutboundStatisticsReportCustomer,
        module='hrp_report', type_='model')
    Pool.register(
        HrpStockReportWizard,
        PriceAdjustmentWizard,
        PriceProfitLossWizard,
        HrpExpiryLotWizard,
        HrpOutboundStatisticsWizard,
        module='hrp_report', type_='wizard')
