import elasticsearch

class ElasticBackend:
    def __init__(self, url):
        self.url = url
        self.client = elasticsearch.Elasticsearch(hosts=url)
        self.name = "Elasticsearch"

    def get_query(self, where):
        if where is None:
            return {"match_all": {}}

        if where["op"] == "=":
            left, right = where["args"]
            return {"term": {left["value"]: right["value"]}}
        elif where["op"] == "and":
            return {
                "bool": {
                    "must": [
                        self.get_query(x) for x in where["args"]
                    ],
                },
            }

    def get_fields(self, select):
        if len(select) == 1 and select[0]["type"] == "star":
            fields = "*"
        elif select:
            fields = [s["value"] for s in select if s["type"] == "name"]

        if fields:
            return fields
        else:
            return None

    def get_aggregation(self, select):
        assert select[0]["type"] == "function"
        func_appl = select[0]["value"]
        type_ = func_appl["name"]
        field = func_appl["arg"]["value"]
        query = {
            f"{type_}_{field}": {
                type_: {
                    "field": field,
                }
            }
        }
        return query

    def translate(self, ir_dct):
        assert ir_dct["type"] == "select"
        body = {}
        index = ir_dct["table"]["value"]

        limit = ir_dct.get("limit")
        if limit is not None:
            body["size"] = limit

        select = ir_dct["columns"]
        fields = self.get_fields(select)
        if not fields:
            body["aggregations"] = self.get_aggregation(select)
            return index, body

        body["_source"] = fields
        where = ir_dct.get("condition")
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
