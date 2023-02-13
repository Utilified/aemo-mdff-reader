""" enem12 for nem-reader-importer """
# import statements
from .record import Record, REQUIRED

__author__ = "Cohen Robinson"
ATTRIBUTES = {}

ELEC_DEM_SUM_ID = 600
ATTRIBUTES[ELEC_DEM_SUM_ID] = [
    ("RecordIndicator", REQUIRED),
    ("NMI", REQUIRED),
    ("MeterSerialNumber", REQUIRED),
    ("ReadDate", REQUIRED),
    ("NMISuffix", REQUIRED),
    ("DailySummation", REQUIRED),
    ("TotalSummation", REQUIRED)
]

WATER_SUM_ID = 610
ATTRIBUTES[WATER_SUM_ID] = ATTRIBUTES[ELEC_DEM_SUM_ID]

ELEC_WATER_SUM_ID = 700
ATTRIBUTES[ELEC_WATER_SUM_ID] = ATTRIBUTES[ELEC_DEM_SUM_ID]

class ElectricityDemandSummation(Record):
    """
    Represenents a Electricty/Demand summation
    record within the ENEM-12 spec.
    """
    RECORD_ID = ELEC_DEM_SUM_ID
    def __init__(self):
        super().__init__(ELEC_DEM_SUM_ID, ATTRIBUTES[ELEC_DEM_SUM_ID])
