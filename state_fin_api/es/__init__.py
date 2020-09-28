import os
from elasticsearch import Elasticsearch


es = None


def get_es():
    global es
    if es is None:
        es = Elasticsearch(hosts=[os.getenv("ES_HOST")])

    return es


def get_supported_states():
    es = get_es()

    res = es.indices.get("*_contribs")

    states = [s[:2] for s in res.keys()]

    return states
