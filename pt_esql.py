#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

from pygments.lexers import SqlLexer

from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer


def main():
    stmt = prompt(
        'Give me some input:\n > ',
        lexer=PygmentsLexer(SqlLexer),
    )
    print(f"You said: {stmt}")


if __name__ == '__main__':
    main()
