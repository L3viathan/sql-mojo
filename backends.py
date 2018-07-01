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

    def __init__(self, url):
        self.url = url
        self.client = elasticsearch.Elasticsearch(hosts=url)
        self.name = "Elasticsearch"

    def get_query(self, where):
        if where is None:
            return {"match_all": {}}

        if "eq" in where:
            left, right = where["eq"]
            return {"term": {left: right}}
        elif "and" in where:
            return {
                "bool": {
                    "must": [
                        self.get_query(x) for x in where["and"]
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

    def get_aggregation(self, select):
        type, field = select.popitem()
        query = {
            f"{type}_{field}": {
                type: {
                    "field": field,
                }
            }
        }
        return query

    def translate(self, ir_dct):
        body = {}
        index = ir_dct["from"]

        limit = ir_dct.get("limit")
        if limit is not None:
            body["size"] = limit

        select = ir_dct["select"]
        fields = self.get_fields(select)
        if not fields:
            body["aggregations"] = self.get_aggregation(select)
            return index, body

        body["_source"] = fields
        where = ir_dct.get("where")
        body["query"] = self.get_query(where)

        return index, body

    def query(self, data):
        try:
            index, query = self.translate(data)

            response = self.client.search(index=index, body=query)
            result = response.get("aggregations")
            if result is None:
                result = response["hits"]["hits"]

        except elasticsearch.exceptions.RequestError as exc:
            result = exc.info["error"]["root_cause"][0]["reason"]

        return result

    def get_tables(self):
        return [t["index"] for t in self.client.cat.indices(format="json")]


def load(type_, url):
    if type_ == "elastic" or type_ is None and ":9200" in url:
        return ElasticBackend(url)
    else:
        return DummyBackend(url)
