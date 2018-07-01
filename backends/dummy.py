# -*- coding: utf-8 -*-

import click

import moz_sql_parser

from prompt_toolkit.formatted_text import HTML

import sql


class DummyBackend:

    def __init__(self):
        self.name = "Dummy"

    def get_tables(self):
        return "foo bar bat".split()

    def query(self, data):
        return data


@click.command()
@click.pass_context
def dummy(ctx):
    """Dummy backend"""
    backend = DummyBackend()
    while True:
        try:
            stmt = ctx.obj["session"].prompt(
                "eSQL> ",
                bottom_toolbar=HTML(f"{backend.name}"),
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
