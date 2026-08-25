import sqlite3
import zipfile
import os

DB_PATH = "afghanistan.db"
ZIP_FILE = "AF.zip"


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY,
            name TEXT,
            ascii_name TEXT,
            alternate_names TEXT,
            latitude REAL,
            longitude REAL,
            feature_class TEXT,
            feature_code TEXT,
            country_code TEXT,
            admin1_code TEXT,
            admin2_code TEXT,
            population INTEGER
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_places_name
        ON places(name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_places_ascii
        ON places(ascii_name)
    """)

    conn.commit()


def import_data():
    if not os.path.exists(ZIP_FILE):
        raise FileNotFoundError(
            "فایل AF.zip در کنار برنامه پیدا نشد."
        )

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)

    cursor = conn.cursor()

    with zipfile.ZipFile(ZIP_FILE, "r") as z:
        with z.open("AF.txt") as file:

            for line in file:
                row = line.decode("utf-8").rstrip("\n").split("\t")

                if len(row) < 19:
                    continue

                try:
                    population = int(row[14] or 0)
                except ValueError:
                    population = 0

                cursor.execute("""
                    INSERT OR REPLACE INTO places (
                        id,
                        name,
                        ascii_name,
                        alternate_names,
                        latitude,
                        longitude,
                        feature_class,
                        feature_code,
                        country_code,
                        admin1_code,
                        admin2_code,
                        population
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row[0]),
                    row[1],
                    row[2],
                    row[3],
                    float(row[4]),
                    float(row[5]),
                    row[6],
                    row[7],
                    row[8],
                    row[10],
                    row[11],
                    population
                ))

    conn.commit()
    conn.close()

    print("🇦🇫 اطلاعات GeoNames وارد دیتابیس شد.")


if __name__ == "__main__":
    import_data()
