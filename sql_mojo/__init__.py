#!/usr/bin/env python3
"""
Demonstration of how the input can be indented.
"""
import json

import click
import Levenshtein

from pygments.lexers import JsonLexer
from pygments.styles import get_style_by_name

from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML, PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings

from sql_mojo_parser import yacc

import sql_mojo.sql as sql
import sql_mojo.backends as backends
from sql_mojo.pager import pager
from tabulate import tabulate

json_lexer = JsonLexer()
style = style_from_pygments_cls(get_style_by_name("monokai"))


def tabularize(list_of_dicts):
    if not list_of_dicts:
        return []
    header = list(list_of_dicts[0].keys())

    def row_iterator():
        for row in list_of_dicts:
            yield [row[key] for key in header]

    return row_iterator(), header


def is_flat(something):
    return all(
        all(not isinstance(row[key], (list, dict)) for key in row) for row in something
    )


def render(output):
    dump = json.dumps(output, indent=4)
    tokens = list(json_lexer.get_tokens(dump))

    with pager(options="-FRSX") as less:
        if is_flat(output):
            table = tabulate(*tabularize(output), tablefmt="psql").encode("utf-8")
            less.write(table)
        else:
            print_formatted_text(PygmentsTokens(tokens), style=style, file=less)


@click.command()
@click.option("--type", type=str, default=None)
@click.argument("url", type=str, required=True)
def main(type, url):
    try:
        backend = backends.load(type, url)
    except ValueError as ex:
        print(ex.args[0])
        backends.list()
        return
    completer = sql.SQLCompleter(tables=backend.get_tables())

    bindings = KeyBindings()

    @bindings.add(" ")
    def _(event):
        buffer = event.app.current_buffer
        word = buffer.document.get_word_before_cursor()
        if word is not None:
            for comp in sql.keywords:
                if Levenshtein.ratio(word.lower(), comp.lower()) >= 0.75:
                    buffer.delete_before_cursor(count=len(word))
                    buffer.insert_text(comp)
                    break
        buffer.insert_text(" ")

    history = FileHistory(".sqlmojo_history")
    session = PromptSession(
        ">",
        lexer=PygmentsLexer(sql.SQLLexer),
        completer=completer,
        complete_while_typing=False,
        history=history,
        validator=sql.SQLValidator(),
        validate_while_typing=False,
        bottom_toolbar=HTML(f"{backend.name}: <b>{url}</b>"),
        key_bindings=bindings,
        style=style,
    )

    while True:
        try:
            stmt = session.prompt("eSQL> ").rstrip(";")
            if not stmt.strip():
                continue

            ir_dct = yacc.parse(stmt)
            result = backend.query(ir_dct)
            render(result)

        except EOFError:
            break


if __name__ == "__main__":
    main()
