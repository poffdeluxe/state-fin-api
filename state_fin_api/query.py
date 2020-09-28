import datetime
import copy

DEFAULT_LIMIT = 500

DEFAULT_START_DATE = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d").date()

DEFAULT_SUMMARY_QUERY = {
    "size": 0,
    "track_total_hits": True,
    "aggs": {
        "contribution_stats": {"stats": {"field": "amount"}},
        "contribution_by_type": {
            "terms": {"field": "type", "size": 5},
            "aggs": {
                "1": {"stats": {"field": "amount"}},
            },
        },
        "latest_contribution": {"max": {"field": "contribution_date"}},
    },
    "query": {"bool": {"filter": []}},
}

DEFAULT_RECORDS_QUERY = {
    "size": DEFAULT_LIMIT,
    "from": 0,
    "track_total_hits": True,
    "sort": [{"contribution_date": {"order": "desc"}}],
    "query": {"bool": {"filter": []}},
}


def build_summary_query(
    start_date=DEFAULT_START_DATE,
    end_date=datetime.datetime.now(),
    filters=[],
    addtl_aggs={},
    include_sample=False,
):
    query = copy.deepcopy(DEFAULT_SUMMARY_QUERY)

    if include_sample:
        query["size"] = 1

    # Add time range
    query["query"]["bool"]["filter"].append(
        {"range": {"contribution_date": {"gte": start_date, "lte": end_date}}}
    )

    # Add additional aggregations
    query["aggs"].update(addtl_aggs)

    query["query"]["bool"]["filter"].extend(filters)

    return query


def build_records_query(
    start_date=DEFAULT_START_DATE,
    end_date=datetime.datetime.now(),
    size=DEFAULT_LIMIT,
    offset=0,
    filters=[],
):
    query = copy.deepcopy(DEFAULT_RECORDS_QUERY)

    # "legacy" pagination
    query["size"] = size
    query["from"] = offset

    # Add time range
    query["query"]["bool"]["filter"].append(
        {"range": {"contribution_date": {"gte": start_date, "lte": end_date}}}
    )

    query["query"]["bool"]["filter"].extend(filters)

    return query


def get_available_districts_aggs():
    return {
        "districts_by_house": {
            "terms": {"field": "candidate.house.keyword", "size": 150},
            "aggs": {
                "districts": {
                    "terms": {
                        "field": "candidate.district",
                        "size": 150,
                        "order": {"_key": "asc"},
                    }
                }
            },
        }
    }


def get_candidates_for_district_aggs():
    return {
        "candidates": {
            "terms": {"field": "candidate.candidate_id.keyword", "size": 150},
            "aggs": {
                "candidate_stats": {"stats": {"field": "amount"}},
                "candidate_name": {
                    "terms": {"field": "candidate.name.keyword", "size": 1}
                },
            },
        }
    }


def get_associated_filers_aggs():
    return {
        "associated_filers": {
            "terms": {"field": "filer.filer_id.keyword", "size": 10},
            "aggs": {
                "filer_stats": {"stats": {"field": "amount"}},
                "filer_name": {"terms": {"field": "filer.name.keyword", "size": 10}},
            },
        }
    }


def get_district_filter_set(house, district):
    return [
        {"term": {"candidate.house.keyword": house}},
        {"match": {"candidate.district": int(district)}},
    ]


def get_filer_filter_set(filer_id):
    return [
        {"term": {"filer.filer_id.keyword": filer_id}},
    ]


def get_candidate_filter_set(candidate_id):
    return [
        {"term": {"candidate.candidate_id.keyword": candidate_id}},
    ]