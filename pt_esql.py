#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""

from prompt_toolkit import prompt


def main():
    stmt = prompt('Give me some input:\n > ')
    print(f"You said: {stmt}")


if __name__ == '__main__':
    main()
