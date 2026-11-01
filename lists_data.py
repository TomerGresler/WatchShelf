import sqlite3
import os
conn = sqlite3.connect(os.environ.get('WATCHSHELF_DB', 'database.db'), check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def create_list(name):
    c.execute("SELECT * FROM lists WHERE name = ?", (name,))
    existing = c.fetchone()
    if existing is not None:
        return None  # a list with this name already exists

    c.execute("INSERT INTO lists(name) VALUES (?)", (name,))
    conn.commit()

    c.execute("SELECT * FROM lists WHERE name = ?", (name,))
    new_list = c.fetchone()
    return {"id": new_list["id"], "name": new_list["name"]}

def get_all_lists():
    c.execute("SELECT * FROM lists")
    rows = c.fetchall()
    lists = []
    for row in rows:
        lists.append({"id": row["id"], "name": row["name"]})
    return lists

def get_list_by_name_partialmatch(name):
    c.execute("SELECT * FROM lists WHERE name LIKE ?", (f"%{name}%",))
    rows = c.fetchall()
    lists = []
    for row in rows:
        lists.append({"id": row["id"], "name": row["name"]})
    return lists