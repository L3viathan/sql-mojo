#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

import json
import subprocess
from io import BytesIO

import click
import moz_sql_parser
import Levenshtein

from pygments.lexers import JsonLexer
from pygments.styles import get_style_by_name

from prompt_toolkit.renderer import (
    print_formatted_text as renderer_print_formatted_text
)
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML, PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings

import sql
import backends


@click.command()
@click.option("--url", type=str, required=True)
@click.option("--type", type=str, default=None)
def main(url, type):
    backend = backends.load(type, url)
    completer = sql.SQLCompleter(tables=backend.get_tables())
    json_lexer = JsonLexer()
    bindings = KeyBindings()
    style = style_from_pygments_cls(get_style_by_name("monokai"))

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

    history = FileHistory(".pt_esql_history")
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

            ir_dct = moz_sql_parser.parse(stmt)
            result = backend.search(ir_dct)
            dump = json.dumps(result, indent=4)
            tokens = list(json_lexer.get_tokens(dump))

            bytesio = BytesIO()
            bytesio.encoding = "UTF-8"
            output = Vt100_Output(bytesio, get_size)
            renderer_print_formatted_text(
                output, PygmentsTokens(tokens), style=style
            )

            # Pager Options:
            # -F: Quit less if the entire content can be displayed on the first
            #     page.
            # -R: Display raw control characters.
            # -S: Disable line wrapping.
            # -X: Avoid clearing the screen on de-initialization. This in
            #     combination with the -F option allows a content sensitive
            #     triggering of less.
            subprocess.run(["less", "-FRSX"], input=bytesio.getvalue())
        except EOFError:
            break


if __name__ == "__main__":
    main()
