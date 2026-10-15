"""Small parameterized database adapter for SQLite and MySQL."""
import os
import sqlite3
from contextlib import contextmanager
from .config import ROOT, load_env


class Database:
    def __init__(self, backend=None, path=None):
        load_env()
        self.backend = backend or os.getenv("DB_BACKEND", "sqlite")
        if self.backend == "sqlite":
            target = path or ROOT / "data/riskflow.db"
            if str(target) != ":memory:":
                target = __import__("pathlib").Path(target)
                target.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(target), timeout=30)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys=ON")
        elif self.backend == "mysql":
            try:
                import mysql.connector
            except ImportError as exc:
                raise RuntimeError("Install requirements-mysql.txt before using MySQL") from exc
            self.connection = mysql.connector.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")), user=os.getenv("MYSQL_USER", "riskflow"), password=os.getenv("MYSQL_PASSWORD", ""), database=os.getenv("MYSQL_DATABASE", "riskflow"), autocommit=False)
        else:
            raise ValueError("DB_BACKEND must be sqlite or mysql")

    def execute(self, sql, values=()):
        cursor = self.connection.cursor(dictionary=True) if self.backend == "mysql" else self.connection.cursor()
        cursor.execute(sql.replace("?", "%s") if self.backend == "mysql" else sql, values)
        return cursor

    def rows(self, sql, values=()):
        cursor = self.execute(sql, values)
        rows = [dict(x) for x in cursor.fetchall()]
        cursor.close()
        return rows

    def insert_many(self, table, rows):
        if not rows:
            return
        keys = list(rows[0])
        statement = f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join(['?'] * len(keys))})"
        cursor = self.connection.cursor()
        if self.backend == "mysql":
            statement = statement.replace("?", "%s")
        cursor.executemany(statement, [tuple(row[key] for key in keys) for row in rows])
        cursor.close()

    def initialize(self):
        source = (ROOT / "sql" / f"schema_{self.backend}.sql").read_text(encoding="utf-8")
        if self.backend == "sqlite":
            self.connection.executescript(source)
        else:
            for statement in source.split("-- statement"):
                if statement.strip():
                    self.execute(statement.strip()).close()
            self.connection.commit()

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
