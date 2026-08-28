import sqlite3


DB_NAME = "afghanistan.db"


def get_connection():

    conn = sqlite3.connect(
        DB_NAME
    )

    return conn


def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            category TEXT NOT NULL,

            content TEXT NOT NULL,

            keywords TEXT DEFAULT ''

        )
    """)

    conn.commit()

    conn.close()


def add_document(
    title,
    category,
    content,
    keywords=""
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documents
        (
            title,
            category,
            content,
            keywords
        )
        VALUES (?, ?, ?, ?)
    """, (
        title,
        category,
        content,
        keywords
    ))

    conn.commit()

    conn.close()


def search_documents(
    query,
    category=None
):

    query = str(
        query
    ).strip()

    if not query:
        return []

    conn = get_connection()

    cursor = conn.cursor()

    search_text = (
        f"%{query}%"
    )

    if category:

        cursor.execute("""

            SELECT
                id,
                title,
                category,
                content

            FROM documents

            WHERE
                (
                    title LIKE ?
                    OR category LIKE ?
                    OR content LIKE ?
                    OR keywords LIKE ?
                )

                AND category = ?

            LIMIT 50

        """, (
            search_text,
            search_text,
            search_text,
            search_text,
            category
        ))

    else:

        cursor.execute("""

            SELECT
                id,
                title,
                category,
                content

            FROM documents

            WHERE
                title LIKE ?
                OR category LIKE ?
                OR content LIKE ?
                OR keywords LIKE ?

            LIMIT 50

        """, (
            search_text,
            search_text,
            search_text,
            search_text
        ))

    results = cursor.fetchall()

    conn.close()

    return results


# =========================================================
# ساخت دیتابیس در اولین اجرا
# =========================================================

init_db()
