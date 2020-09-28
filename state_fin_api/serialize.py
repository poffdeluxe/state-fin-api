import humps


def serialize_summary_result(raw_result, start_date, end_date):
    contrib_by_type = {
        "individual": {"count": 0, "total_amount": 0, "avg_amount": 0},
        "entity": {"count": 0, "total_amount": 0, "avg_amount": 0},
        "unknown": {"count": 0, "total_amount": 0, "avg_amount": 0},
    }

    contrib_by_type_list = raw_result["aggregations"]["contribution_by_type"]["buckets"]
    for bucket in contrib_by_type_list:
        bucket_key = bucket["key"].lower()

        if bucket_key in contrib_by_type:
            contrib_by_type[bucket_key]["count"] = bucket["1"]["count"]
            contrib_by_type[bucket_key]["total_amount"] = bucket["1"]["sum"]
            contrib_by_type[bucket_key]["avg_amount"] = bucket["1"]["avg"]

    latest_at = None
    if "value_as_string" in raw_result["aggregations"]["latest_contribution"]:
        latest_at = raw_result["aggregations"]["latest_contribution"]["value_as_string"]

    return {
        "count": raw_result["aggregations"]["contribution_stats"]["count"],
        "total_amount": raw_result["aggregations"]["contribution_stats"]["sum"],
        "avg_amount": raw_result["aggregations"]["contribution_stats"]["avg"],
        "latest_at": latest_at,
        "contribution_by_type": contrib_by_type,
        "query": {
            "start_date": start_date,
            "end_date": end_date,
            "timed_out": raw_result["timed_out"],
            "took": raw_result["took"],
        },
    }


def serialize_records_result(raw_result, start_date, end_date, offset, limit):
    return {
        "records": [humps.decamelize(h["_source"]) for h in raw_result["hits"]["hits"]],
        "query": {
            "start_date": start_date,
            "end_date": end_date,
            "offset": offset,
            "limit": limit,
            "timed_out": raw_result["timed_out"],
            "took": raw_result["took"],
            "total": raw_result["hits"]["total"]["value"],
            "hits": len(raw_result["hits"]["hits"]),
        },
    }


def serialize_filer_result(raw_result):
    if len(raw_result["hits"]["hits"]) == 0:
        return {}

    record = raw_result["hits"]["hits"][0]["_source"]

    filer_data = record["filer"]
    filer_data["candidate"] = record["candidate"] if record["candidate"] else None

    return humps.decamelize(filer_data)


def serialize_candidate_result(raw_result):
    if len(raw_result["hits"]["hits"]) == 0:
        return {}

    record = raw_result["hits"]["hits"][0]["_source"]

    return humps.decamelize(record["candidate"])


def serialize_filers_associated_with_candidate(raw_result):
    associated_filers = {}

    for bucket in raw_result["aggregations"]["associated_filers"]["buckets"]:
        associated_filers[bucket["key"]] = {
            "name": bucket["filer_name"]["buckets"][0]["key"],
            "count": bucket["filer_stats"]["count"],
            "total_amount": bucket["filer_stats"]["sum"],
            "avg_amount": bucket["filer_stats"]["avg"],
        }

    return {"associated_filers": associated_filers}


def serialize_candidates_for_district(raw_result):
    candidates = {}

    for bucket in raw_result["aggregations"]["candidates"]["buckets"]:
        candidates[bucket["key"]] = {
            "name": bucket["candidate_name"]["buckets"][0]["key"],
            "count": bucket["candidate_stats"]["count"],
            "total_amount": bucket["candidate_stats"]["sum"],
            "avg_amount": bucket["candidate_stats"]["avg"],
        }

    return {"candidates": candidates}


def serialize_state_districts(raw_result):
    # TODO: Special case nebraska (has only one house in legislature)

    lower_districts = []
    upper_districts = []

    for bucket in raw_result["aggregations"]["districts_by_house"]["buckets"]:
        district_buckets = bucket["districts"]["buckets"]
        districts = [d["key"] for d in district_buckets]

        if bucket["key"] == "lower":
            lower_districts = districts
        else:
            upper_districts = districts

    return {"districts": {"lower": lower_districts, "upper": upper_districts}}
