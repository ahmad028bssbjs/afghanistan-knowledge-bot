import sqlite3
import os

DB_PATH = "afghanistan.db"


def connect_db():
    return sqlite3.connect(DB_PATH)


def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            content TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_document(title, category, content):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documents (title, category, content)
        VALUES (?, ?, ?)
    """, (title, category, content))

    conn.commit()
    conn.close()


def search_documents(query):
    conn = connect_db()
    cursor = conn.cursor()

    search = f"%{query}%"

    cursor.execute("""
        SELECT id, title, category, content
        FROM documents
        WHERE title LIKE ?
           OR category LIKE ?
           OR content LIKE ?
        LIMIT 20
    """, (search, search, search))

    results = cursor.fetchall()

    conn.close()
    return results


create_database()
