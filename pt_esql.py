#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

import json
import subprocess
from contextlib import redirect_stdout
from io import BytesIO

import click
import moz_sql_parser
import pyparsing
import Levenshtein
import elasticsearch

from pygments.lexers import SqlLexer, JsonLexer
from pygments.styles import get_style_by_name
from pygments.token import Token

from prompt_toolkit import prompt
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.formatted_text import HTML, PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings



def get_size():
    x, y = subprocess.check_output(["stty", "size"]).decode("utf8").split()
    return int(x), int(y)


completions = [
    "SELECT", "FROM", "WHERE", "ORDER BY", "AND", "OR", "LIMIT",
]

sql_completer =  WordCompleter(completions, ignore_case=True)


class SQLLexer(SqlLexer):
    def get_tokens_unprocessed(self, text, stack=('root',)):
        for i, typ, val in super().get_tokens_unprocessed(text, stack=stack):
            if typ == Token.Literal.String.Symbol:
                yield i, Token.Literal.String.Double, val
            else:
                yield i, typ, val


class SQLValidator(Validator):

    def validate(self, document):
        if not document.text.strip():
            return
        text = document.text.rstrip(";")
        try:
            result = moz_sql_parser.parse(text)
            if "from" not in result:
                raise pyparsing.ParseException(text, len(text), "Expecting from")
        except pyparsing.ParseException as exc:
            raise ValidationError(
                message=str(exc),
                cursor_position=exc.args[1],
            )


def get_query(where):
    if where is None:
        return {
            "match_all": {}
    }

def get_source(select):
    if isinstance(select, dict):
        return [select["value"]]
    else:
        return [s["value"] for s in select]


def translate_to_elastic_query(ir_dct):
    body = {}
    body["query"] = get_query(ir_dct.get("where"))
    if ir_dct["select"] != "*":
        body["_source"] = get_source(ir_dct["select"])
    body["size"] = ir_dct.get("limit", 10)
    index = ir_dct["from"]
    return index, body


@click.command()
@click.option(
    "--url",
    type=str,
    required=True,
)
def main(url):
    client = elasticsearch.Elasticsearch(hosts=url)
    json_lexer = JsonLexer()
    bindings = KeyBindings()
    style = style_from_pygments_cls(get_style_by_name("monokai"))
    @bindings.add(" ")
    def _(event):
        buffer = event.app.current_buffer
        word = buffer.document.get_word_before_cursor()
        if word is not None:
            for comp in completions:
                if Levenshtein.distance(word.lower(), comp.lower()) < 2:
                    buffer.delete_before_cursor(count=len(word))
                    buffer.insert_text(comp)
                    break
        buffer.insert_text(" ")

    history = FileHistory(".pt_esql_history")
    session = PromptSession(
        ">",
        lexer=PygmentsLexer(SQLLexer),
        completer=sql_completer,
        complete_while_typing=False,
        history=history,
        validator=SQLValidator(),
        validate_while_typing=False,
        bottom_toolbar=HTML(f"URL: <b>{url}</b>"),
        key_bindings=bindings,
        style=style,
    )

    while True:
        try:
            stmt = session.prompt(
                'Give me some input:\n > ',
            ).rstrip(';')
            if not stmt.strip():
                continue

            ir_dct = moz_sql_parser.parse(stmt)
            index, query = translate_to_elastic_query(ir_dct)
            result = client.search(index=index, body=query)
            dump = json.dumps(result["hits"]["hits"], indent=4)
            tokens = list(json_lexer.get_tokens(dump))

            if get_size()[1] < dump.count("\n") -1:
                bytesio = BytesIO()
                bytesio.encoding = "UTF-8"
                output = Vt100_Output(bytesio, get_size)
                renderer_print_formatted_text(
                    output,
                    PygmentsTokens(tokens),
                    style=style,
                )

                subprocess.run(
                    ["less", "-R"],
                    input=bytesio.getvalue(),
                )
            else:
                print_formatted_text(
                    PygmentsTokens(tokens),
                    style=style,
                )

        except EOFError:
            break


if __name__ == '__main__':
    main()
