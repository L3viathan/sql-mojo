import sqlite3

class SQLiteBackend:
    name = "sqlite"

    def __init__(self, file):
        self.conn = sqlite3.connect(file)

    def get_tables(self):
        c = self.conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in c.fetchall()]

    def query(self, data):
        c = self.conn.cursor()
        c.execute(data["raw"])
        return [
            {k[0]: v for v, k in zip(row, c.description)}
            for row in c
        ]

    @staticmethod
    def detect(url):
        return url.endswith(".db")
