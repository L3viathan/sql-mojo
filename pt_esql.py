#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

from pygments.lexers import SqlLexer

from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.completion import WordCompleter


sql_completer =  WordCompleter(
    [
        "SELECT", "FROM", "WHERE", "ORDER BY", "AND", "OR",
    ],
    ignore_case=True,
)


def main():
    session = PromptSession(
        ">",
        lexer=PygmentsLexer(SqlLexer),
        completer=sql_completer,
        complete_while_typing=False,
    )

    while True:
        try:
            stmt = session.prompt(
                'Give me some input:\n > ',
            )
            print(f"You said: {stmt}")
        except EOFError:
            break

if __name__ == '__main__':
    main()
