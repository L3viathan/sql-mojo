from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.completion import Completer, Completion
from pygments.lexers import SqlLexer
from pygments.token import Token

from sql_mojo_parser import yacc

keywords = ["SELECT", "FROM", "WHERE", "ORDER BY", "AND", "OR", "LIMIT"]


class SQLCompleter(Completer):
    def __init__(self, tables):
        super().__init__()
        self.tables = tables

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()

        if word:
            for keyword in keywords:
                if keyword.lower().startswith(word.lower()):
                    yield Completion(keyword, start_position=-len(word))
        else:
            _, __, previous = document.text[:-1].rpartition(" ")
            if previous.lower() == "from":
                for tbl in self.tables:
                    yield Completion(tbl, start_position=0)


class SQLLexer(SqlLexer):
    def get_tokens_unprocessed(self, text, stack=("root",)):
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
            result = yacc.parse(text)
            if "index" not in result:
                raise SyntaxError(text, len(text), "Expecting from")
        except SyntaxError as exc:
            raise ValidationError(message=str(exc)) #, cursor_position=exc.args[1])
