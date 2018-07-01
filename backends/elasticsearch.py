# -*- coding: utf-8 -*-

import click

import moz_sql_parser

from elasticsearch import Elasticsearch

from prompt_toolkit.formatted_text import HTML

import sql


class ElasticBackend:

    def __init__(self, url):
        self.url = url
        self.client = Elasticsearch(hosts=url)
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


@click.command()
@click.option("--url", type=str, required=True)
@click.pass_context
def elasticsearch(ctx, url):
    """ Elasticsearch backend"""
    backend = ElasticBackend(url)
    while True:
        try:
            stmt = ctx.obj["session"].prompt(
                "eSQL> ",
                bottom_toolbar=HTML(f"{backend.name}: <b>{url}</b>"),
                completer=sql.SQLCompleter(tables=backend.get_tables()),
                complete_while_typing=False,
            ).rstrip(";")
            if not stmt.strip():
                continue

            ir_dct = moz_sql_parser.parse(stmt)
            result = backend.query(ir_dct)
            ctx.obj["render"](result)

        except EOFError:
            break
