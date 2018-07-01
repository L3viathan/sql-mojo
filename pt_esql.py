#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

import importlib
import json
import pkgutil

import click
import Levenshtein

from pygments.lexers import JsonLexer
from pygments.styles import get_style_by_name

from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings

import sql
from pager import pager
import backends

json_lexer = JsonLexer()
style = style_from_pygments_cls(get_style_by_name("monokai"))


def render(output):
    dump = json.dumps(output, indent=4)
    tokens = list(json_lexer.get_tokens(dump))

    with pager(options="-FRSX") as less:
        print_formatted_text(
            PygmentsTokens(tokens),
            style=style,
            file=less,
        )


def load_commands():
    """ Loads supported backends and registers the corresponding commands in
    the main command group.

    Note: This function assumes that the command to register has the same name
          as corresponding module in the backends package.
    """
    for _, modname, _ in pkgutil.iter_modules(backends.__path__):
        import_path = ".".join([backends.__name__, modname])
        backend = importlib.import_module(import_path)
        command = getattr(backend, modname)
        cli.add_command(command)


@click.group()
@click.pass_context
def cli(ctx):
    """ Foo baz Bar"""
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

    history = FileHistory(".pt_esql_history")

    ctx.obj = {
        "session": PromptSession(
            ">",
            lexer=PygmentsLexer(sql.SQLLexer),
            history=history,
            validator=sql.SQLValidator(),
            validate_while_typing=False,
            key_bindings=bindings,
            style=style,
        ),
        "render": render,
    }


if __name__ == "__main__":
    load_commands()
    cli()
