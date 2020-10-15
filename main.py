import datetime
import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Body, HTTPException

from elasticsearch import Elasticsearch

import state_fin_api
from state_fin_api.es import get_es
from state_fin_api.query import (
    build_contrib_summary_query,
    build_contrib_records_query,
    build_report_records_query,
    get_district_filter_set,
    get_available_districts_aggs,
    get_candidates_for_district_aggs,
    get_filer_filter_set,
    get_candidate_filter_set,
    get_associated_filers_aggs,
    DEFAULT_LIMIT,
    DEFAULT_START_DATE,
)
from state_fin_api.serialize import (
    serialize_contrib_summary_result,
    serialize_records_result,
    serialize_filer_result,
    serialize_candidate_result,
    serialize_candidates_for_district,
    serialize_filers_associated_with_candidate,
    serialize_state_districts,
)
from state_fin_api.types import (
    StateCode,
    HouseLevel,
    Summary,
    StateSummary,
    DistrictSummary,
    FilerSummary,
    CandidateSummary,
    Contributions,
    Reports,
)

load_dotenv()


app = FastAPI(
    title="state-fin-api",
    description="API for retrieving finance information regarding state legislature campaigns",
)

env = os.getenv("API_ENV", "dev")


def get_contrib_index_from_state_code(state_code: StateCode):
    global env
    return f"{state_code}_contribs_{env}"


def get_report_index_from_state_code(state_code: StateCode):
    global env
    return f"{state_code}_reports_{env}"


def get_wildcard_contrib_index():
    global env
    return f"*_contribs_{env}"


def get_wildcard_report_index():
    global env
    return f"*_reports_{env}"


@app.get("/", response_model=Summary)
async def get_complete_summary(
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    es: Elasticsearch = Depends(get_es),
):

    query = build_contrib_summary_query(start_date, end_date)
    raw_res = es.search(query, get_wildcard_contrib_index())

    return serialize_contrib_summary_result(raw_res, start_date, end_date)


@app.get("/reports", response_model=Reports)
async def get_all_reports(
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.datetime.now(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):

    query = build_report_records_query(start_date, end_date, limit, offset)

    raw_res = es.search(query, get_wildcard_report_index())

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}", response_model=StateSummary)
async def get_state_summary(
    state_code: StateCode,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    es: Elasticsearch = Depends(get_es),
):

    district_aggs = get_available_districts_aggs()

    query = build_contrib_summary_query(start_date, end_date, addtl_aggs=district_aggs)
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    result = serialize_contrib_summary_result(raw_res, start_date, end_date)
    result.update(serialize_state_districts(raw_res))

    return result


@app.get("/{state_code}/filer/{filer_id}", response_model=FilerSummary)
async def get_filer_summary(
    state_code: StateCode,
    filer_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    es: Elasticsearch = Depends(get_es),
):
    filer_filter_set = get_filer_filter_set(filer_id)

    query = build_contrib_summary_query(
        start_date, end_date, filters=filer_filter_set, include_sample=True
    )
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    filer = serialize_filer_result(raw_res)
    if not filer:
        # If we didn't find a filer in our result set, throw a 404
        raise HTTPException(
            status_code=404, detail="Filer not found within query parameters"
        )
    result = serializ_contrib_summary_result(raw_res, start_date, end_date)
    result.update(filer)

    return result


@app.get("/{state_code}/filer/{filer_id}/contribs", response_model=Contributions)
async def get_filer_contrib_records(
    state_code: StateCode,
    filer_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.datetime.now(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    filer_filter_set = get_filer_filter_set(filer_id)

    query = build_contrib_records_query(
        start_date, end_date, limit, offset, filer_filter_set
    )

    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}/filer/{filer_id}/reports", response_model=Reports)
async def get_filer_report_records(
    state_code: StateCode,
    filer_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.datetime.now(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    filer_filter_set = get_filer_filter_set(filer_id)

    query = build_report_records_query(
        start_date, end_date, limit, offset, filer_filter_set
    )

    raw_res = es.search(query, get_report_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}/candidate/{candidate_id}", response_model=CandidateSummary)
async def get_candidate_summary(
    state_code: StateCode,
    candidate_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    es: Elasticsearch = Depends(get_es),
):
    candidate_filter_set = get_candidate_filter_set(candidate_id)
    associated_filers_agg = get_associated_filers_aggs()

    query = build_contrib_summary_query(
        start_date,
        end_date,
        filters=candidate_filter_set,
        addtl_aggs=associated_filers_agg,
        include_sample=True,
    )
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    result = serialize_contrib_summary_result(raw_res, start_date, end_date)

    candidate = serialize_candidate_result(raw_res)

    if not candidate:
        # If we didn't find a candidate in our result set, throw a 404
        raise HTTPException(
            status_code=404, detail="Candidate not found within query parameters"
        )

    result.update(candidate)
    result.update(serialize_filers_associated_with_candidate(raw_res))

    return result


@app.get(
    "/{state_code}/candidate/{candidate_id}/contribs", response_model=Contributions
)
async def get_candidate_contrib_records(
    state_code: StateCode,
    candidate_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    candidate_filter_set = get_candidate_filter_set(candidate_id)

    query = build_contrib_records_query(
        start_date, end_date, limit, offset, candidate_filter_set
    )
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}/candidate/{candidate_id}/reports", response_model=Reports)
async def get_candidate_report_records(
    state_code: StateCode,
    candidate_id: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    candidate_filter_set = get_candidate_filter_set(candidate_id)

    query = build_report_records_query(
        start_date, end_date, limit, offset, candidate_filter_set
    )
    raw_res = es.search(query, get_report_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}/{house}/{district}", response_model=DistrictSummary)
async def get_seat_summary(
    state_code: StateCode,
    house: HouseLevel,
    district: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    es: Elasticsearch = Depends(get_es),
):
    candidates_for_district_aggs = get_candidates_for_district_aggs()

    district_filter_set = get_district_filter_set(house.value, district)
    query = build_contrib_summary_query(
        start_date,
        end_date,
        district_filter_set,
        addtl_aggs=candidates_for_district_aggs,
    )
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    result = serializ_contrib_summary_result(raw_res, start_date, end_date)
    result.update(serialize_candidates_for_district(raw_res))

    return result


@app.get("/{state_code}/{house}/{district}/contribs", response_model=Contributions)
async def get_seat_contrib_records(
    state_code: StateCode,
    house: HouseLevel,
    district: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    district_filter_set = get_district_filter_set(house.value, district)
    query = build_contrib_records_query(
        start_date, end_date, limit, offset, district_filter_set
    )
    raw_res = es.search(query, get_contrib_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)


@app.get("/{state_code}/{house}/{district}/reports", response_model=Reports)
async def get_seat_report_records(
    state_code: StateCode,
    house: HouseLevel,
    district: str,
    start_date: Optional[datetime.date] = DEFAULT_START_DATE,
    end_date: Optional[datetime.date] = datetime.date.today(),
    limit: Optional[int] = DEFAULT_LIMIT,
    offset: Optional[int] = 0,
    es: Elasticsearch = Depends(get_es),
):
    district_filter_set = get_district_filter_set(house.value, district)
    query = build_report_records_query(
        start_date, end_date, limit, offset, district_filter_set
    )
    raw_res = es.search(query, get_report_index_from_state_code(state_code))

    return serialize_records_result(raw_res, start_date, end_date, offset, limit)
