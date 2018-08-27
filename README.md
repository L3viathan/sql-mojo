# sql-mojo

SQL _all_ the things!

sql-mojo is a REPL that allows you to interact with a number of backends using an SQL-like syntax.
The currently available backends are:

- ElasticSearch
- file system
- (and a dummy backend for testing)


## Setup

sql-mojo requires Python 3.7+. It can then be installed by cloning this repository and executing

    pip install .

inside it (assuming `pip` points to Python 3.7's pip; you may need to use `pip3` or `python3.7 -m pip`).


## Usage

    sql-mojo --type=TYPE --url=URL

`TYPE` can be ommited if sql-mojo can guess the backend from the `URL`, but it is useful in ambiguos cases.

You should now be in an interactive session with tab completion, auto-correction, history, and many more features (thanks to prompt-toolkit). Press `^D` in an empty line to quit the session.
