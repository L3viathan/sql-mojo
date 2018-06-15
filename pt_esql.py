#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

import moz_sql_parser
import pyparsing

from pygments.lexers import SqlLexer

from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.validation import Validator


sql_completer =  WordCompleter(
    [
        "SELECT", "FROM", "WHERE", "ORDER BY", "AND", "OR",
    ],
    ignore_case=True,
)


def is_valid_sql(text):
    text = text.rstrip(";")
    try:
        moz_sql_parser.parse(text)
    except pyparsing.ParseException:
        return False

    return True


validator = Validator.from_callable(
    is_valid_sql,
    error_message="Syntax Error: Invalid SQL Statement",
    move_cursor_to_end=True,
)


def main():
    history = FileHistory(".pt_esql_history")

    session = PromptSession(
        ">",
        lexer=PygmentsLexer(SqlLexer),
        completer=sql_completer,
        complete_while_typing=False,
        history=history,
        validator=validator,
        validate_while_typing=False,
    )

    while True:
        try:
            stmt = session.prompt(
                'Give me some input:\n > ',
            )
            print(f"You said: {stmt.rstrip(';')}")
        except EOFError:
            break

if __name__ == '__main__':
    main()
