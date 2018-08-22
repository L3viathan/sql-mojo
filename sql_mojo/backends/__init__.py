from .filesystem import FileSystemBackend
from .elasticsearch import ElasticBackend


class DummyBackend:
    def __init__(self, url):
        self.url = url
        self.name = "Dummy"

    def get_tables(self):
        return "foo bar bat".split()

    def query(self, data):
        return data


def load(type_, url):
    if type_ == "elastic" or type_ is None and ":9200" in url:
        return ElasticBackend(url)
    elif type_ == "fs" or type_ is None and ":" not in url:
        return FileSystemBackend(url)
    else:
        return DummyBackend(url)
