from trytond.pool import Pool
from .internal_apply import *
from .internal_retreat import *
from .internal_allocation import *
from .internal_frozen import *
from .internal_relieve import *
from .purchase_request import *
from .shipment import *
from .purchase_purchase import *
from .internal_straight import *
from .purchase_line import *
from .internal_apply_modify import *
from .internal_core_drug import *
from .internal_query import *
from .internal_apply_direct import *
from .internal_core_query import *


def register():
    Pool.register(
        InternalStraights,
        InternalApply,
        InternalRetreat,
        InternalFrozen,
        InternalRelieve,
        InternalAllocation,
        InternalMoveList,
        Move,
        PurchaseRequest,
        ShipmentInternal,
        Purchase,
        TestApply,
        TestRetreat,
        TestFrozen,
        TestStraight,
        PurchaseLine,
        ApplyMoveLook,
        ApplyMoveLookTwo,
        ReturnMoveLook,
        ReturnMoveLookTwo,
        StraightMoveLook,
        FrozenMoveLook,
        InternalApplyModify,
        InternalApplyList,
        ApplyListExhibition,
        InternalCoreDrug,
        InternalQuery,
        InternalDetailed,
        InternalProject,
        ContentInternalProject,
        QueryDepartmentDone,
        QueryPurchaseDone,
        QueryScrapDone,
        QueryFrozenDone,
        QueryAllocationDone,
        QueryReturnDone,
        QueryApplyDone,
        InternalApplyDirect,
        InternalApplyListDirect,
        ApplyListExhibitionDirect,
        InternalCoreQuery,
        InternalCoreDetailed,
        InternalCoreProject,
        ContentInternalCoreProject,
        QueryCoreFrozenDone,
        QueryCoreReturnDone,
        QueryCoreApplyDone,
        module='hrp_internal_delivery', type_='model')
    Pool.register(
        InternalStraightsWizard,
        InternalApplyWizard,
        InternalRetreatWizard,
        InternalFrozenWizard,
        InternalRelieveWizard,
        InternalAllocationWizard,
        ApplyModifyWizard,
        InternalCoreDrugWizard,
        InternalQueryWizard,
        ApplyDirectWizard,
        InternalCoreQueryWizard,
        module='hrp_internal_delivery', type_='wizard')
    Pool.register(
        GeneralJournal,
        CoreDrugReport,
        GeneralCoreJournal,
        module='hrp_internal_delivery', type_='report')
