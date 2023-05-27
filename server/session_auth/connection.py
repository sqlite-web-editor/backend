"""
Define connection as object
"""

from os import path, getcwd, sep
from sys import exit as sys_exit
import logging
import sqlite3  # is used for setup_db
from .sa_types import Path


yes_collection = ("yes", "y", "да", "д")
path_to_db = path.join("session_auth", "sqlite.db")


def setup_db(dbpath: Path) -> None:
    "warning: this function overwrites the database"
    with open(dbpath, "w+", encoding="utf-8"):  # pylint requires hardcoded encoding
        logging.info("Db created")

    with sqlite3.connect(dbpath) as db_connection:
        logging.info("Connected to db")
        query: str = """
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            cookie TEXT,
        )
        """.strip()
        cur: sqlite3.Cursor = db_connection.cursor()
        cur.execute(query)
        logging.info("Table `cookies` created")


def check_db():
    print(getcwd())
    "check db for normality"
    try:
        with sqlite3.connect(path_to_db) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if cur.fetchone() is None: 
                raise EnvironmentError()

    # pylint: disable=broad-except, invalid-name
    except Exception as e:
        logging.error(e)
        logging.info("Cant connected to db. Aborted")

        if input("Setup db? (y/n)").lower().strip() in yes_collection:
            try:
                setup_db(str(path_to_db))
            except Exception as e: # pylint: disable=broad-except, redefined-outer-name, invalid-name
                logging.fatal(e)
                sys_exit(1)

        else:
            sys_exit(1)


    logging.info("Connected to db")
