from enum import Enum
import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class StateCode(str, Enum):
    tx = "tx"
    mi = "mi"


class HouseLevel(str, Enum):
    lower = "lower"
    upper = "upper"


class EntityType(str, Enum):
    individual = "individual"
    entity = "entity"
    unknown = "unknown"


class Filer(BaseModel):
    filer_id: str
    type: str
    name: str


class Candidate(BaseModel):
    candidate_id: str
    name: str
    party: str
    house: HouseLevel
    district: int


class QueryDesc(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    timed_out: bool
    took: int


class ContribQueryDesc(QueryDesc):
    offset: int
    hits: int
    total: int


class ReportQueryDesc(QueryDesc):
    offset: int
    hits: int
    total: int


class Stats(BaseModel):
    count: int
    total_amount: float
    avg_amount: float


class SummaryContributionByType(BaseModel):
    individual: Stats
    entity: Stats
    unknown: Stats


class Summary(Stats):
    latest_at: datetime.datetime

    contribution_by_type: SummaryContributionByType

    query: QueryDesc


class StateDistricts(BaseModel):
    lower: List[str]
    upper: List[str]


class StateSummary(Summary):
    districts: StateDistricts


class CandidateStats(Stats):
    name: str


class FilerStats(CandidateStats):
    pass


class DistrictSummary(Summary):
    candidates: Dict[str, CandidateStats]


class CandidateSummary(Summary, Candidate):
    associated_filers: Dict[str, FilerStats]


class FilerSummary(Summary, Filer):
    candidate: Optional[Candidate] = None


class Contribution(BaseModel):
    filer: Optional[Filer] = None
    candidate: Optional[Candidate] = None

    contribution_id: str
    contribution_date: datetime.datetime
    amount: float
    memo: str
    type: EntityType
    name: str
    city: str
    state: str
    zip: str
    employer: str
    occupation: str
    job_title: str

    addtl_data: Optional[dict]


class Report(BaseModel):
    filer: Optional[Filer] = None
    candidate: Optional[Candidate] = None

    report_id: str
    type: str

    received_date: datetime.datetime

    period_start_date: datetime.datetime
    period_end_date: datetime.datetime

    contributions_amount: float
    expenditures_amount: float
    ending_balance_amount: float


class Contributions(BaseModel):
    records: List[Contribution]
    query: ContribQueryDesc


class Reports(BaseModel):
    records: List[Report]
    query: ReportQueryDesc
