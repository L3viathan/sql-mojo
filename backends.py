import elasticsearch



class DummyBackend:
    def __init__(self, url):
        self.url = url
        self.name = "Dummy"

    def get_tables(self):
        return "foo bar bat".split()

    def search(self, data):
        return data

class ElasticBackend:
    def __init__(self, url):
        self.url = url
        self.client = elasticsearch.Elasticsearch(hosts=url)
        self.name = "ElasticSearch"

    def get_query(self, where):
        if where is None:
            return {"match_all": {}}

        if "eq" in where:
            left, right = where["eq"]
            return {"term": {left: right}}
        elif "and" in where:
            return {"bool": {"must": [self.get_query(x) for x in where["and"]]}}

    def get_source(self, select):
        if isinstance(select, dict):
            return [select["value"]]
        else:
            return [s["value"] for s in select]

    def translate(self, ir_dct):
        body = {}
        body["query"] = self.get_query(ir_dct.get("where"))
        if ir_dct["select"] != "*":
            body["_source"] = self.get_source(ir_dct["select"])
        body["size"] = ir_dct.get("limit", 10)
        index = ir_dct["from"]
        return index, body

    def search(self, data):
        index, query = self.translate(data)
        return client.search(index=index, body=query)["hits"]["hits"]

    def get_tables(self):
        return [t["index"] for t in self.client.cat.indices(format="json")]


def load(type_, url):
    if type_ == "elastic" or type_ is None and ":9200" in url:
        return ElasticBackend(url)
    else:
        return DummyBackend(url)
