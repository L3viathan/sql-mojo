import elasticsearch


class DummyBackend:

    def __init__(self, url):
        self.url = url
        self.name = "Dummy"

    def get_tables(self):
        return "foo bar bat".split()

    def query(self, data):
        return data


class ElasticBackend:

    metrics_aggregation_types = [
        # Functional
        "avg",
        "sum",
        "min",
        "max",
        "stats",
        "cardinality",
        "percentiles",

        # Not working yet.. needs SQL parsing fix
        "top_hits",
        "value_count",
        "extended_stats",
        "percentile_ranks",
        "geo_bounds",
        "geo_centroid",
    ]

    def __init__(self, url, debug=False):
        self.url = url
        self.debug = debug
        self.client = elasticsearch.Elasticsearch(hosts=url, timeout=180)
        self.name = "Elasticsearch"

    def get_query(self, where):
        if where is None:
            return {"match_all": {}}

        query = {"bool": {}}
        if "eq" in where:
            left, right = where["eq"]
            return {"term": {left: right}}
        elif "neq" in where:
            left, right = where["neq"]
            return {"term": {left: right}}
        if "and" in where:
            return {
                "bool": {
                    "must": [
                        self.get_query(x)
                        for x in where["and"]
                        if "eq" in x
                    ],
                    "must_not": [
                        self.get_query(x)
                        for x in where["and"]
                        if "neq" in x
                    ],
                },
            }

    def get_fields(self, select):
        if select == "*":
            fields = select
        elif isinstance(select, list):
            fields = [s["value"] for s in select]
        elif isinstance(select["value"], str):
            fields = [select["value"]]
        else:
            fields = None

        return fields

    def get_aggregation(self, agg_type, field):
        query = {
            f"{agg_type}_{field}": {
                agg_type: {
                    "field": field,
                }
            }
        }
        return query

    def translate(self, ir_dct):
        body = {}
        index = ir_dct["from"]

        count = False
        limit = ir_dct.get("limit")
        if limit is not None:
            body["size"] = limit

        select = ir_dct["select"]
        fields = self.get_fields(select)
        if not fields:
            agg_type, field = select["value"].popitem()
            if agg_type in ElasticBackend.metrics_aggregation_types:
                body["aggregations"] = self.get_aggregation(agg_type, field)
                return index, False, body
            elif agg_type in ["count"]:
                count = True

        if not count:
            body["_source"] = fields

        where = ir_dct.get("where")
        body["query"] = self.get_query(where)

        return index, count, body

    def query(self, data):
        try:
            index, count, query = self.translate(data)

            if self.debug:
                print(query)

            if count:
                response = self.client.count(index=index, body=query)
                return response
            else:
                response = self.client.search(index=index, body=query)

            result = response.get("aggregations")
            if result is None:
                result = response["hits"]["hits"]

        except elasticsearch.exceptions.RequestError as exc:
            result = exc.info["error"]["root_cause"][0]["reason"]

        return result

    def get_tables(self):
        return [t["index"] for t in self.client.cat.indices(format="json")]


def load(type_, url, debug):
    if type_ == "elastic" or type_ is None and ":9200" in url:
        return ElasticBackend(url, debug)
    else:
        return DummyBackend(url)
