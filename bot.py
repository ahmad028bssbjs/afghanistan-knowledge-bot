import os
import json
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from database import search_documents, add_document


logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# -------------------------
# داده‌های آزمایشی
# -------------------------

TEST_DATA = [
    (
        "کابل",
        "جغرافیا",
        "کابل پایتخت افغانستان است."
    ),
    (
        "غزنی",
        "جغرافیا",
        "غزنی یکی از شهرهای تاریخی افغانستان است."
    ),
    (
        "هرات",
        "جغرافیا",
        "هرات یکی از شهرهای مهم تاریخی افغانستان است."
    ),
    (
        "بند کجکی",
        "بندها",
        "بند کجکی در ولایت هلمند افغانستان قرار دارد."
    ),
    (
        "احمدشاه ابدالی",
        "تاریخ",
        "احمدشاه ابدالی بنیان‌گذار امپراتوری درانی بود."
    )
]


def load_test_data():

    for title, category, content in TEST_DATA:

        if not search_documents(title):

            add_document(
                title,
                category,
                content
            )


# -------------------------
# وارد کردن GeoDAR
# -------------------------

def load_reservoirs():

    if not os.path.exists("reservoirs.json"):
        print("reservoirs.json پیدا نشد.")
        return

    with open(
        "reservoirs.json",
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    count = 0

    for item in data:

        if not search_documents(item["title"]):

            add_document(
                item["title"],
                item["category"],
                item["content"]
            )

            count += 1

    print(
        f"🏗 {count} رکورد GeoDAR وارد شد."
    )


# -------------------------
# /start
# -------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🇦🇫 به ربات دانشنامه افغانستان خوش آمدید!\n\n"
        "🔎 نام هر موضوع را برای جستجو بفرست.\n\n"
        "مثال:\n"
        "کابل\n"
        "غزنی\n"
        "بند\n"
        "احمدشاه ابدالی"
    )


# -------------------------
# جستجو
# -------------------------

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return

    results = search_documents(query)

    if not results:

        await update.message.reply_text(
            f"🔎 برای «{query}» چیزی پیدا نشد."
        )

        return

    message = f"🔎 نتایج برای «{query}»:\n\n"

    for i, (_, title, category, content) in enumerate(
        results,
        1
    ):

        message += (
            f"📌 {i}. {title}\n"
            f"📂 {category}\n"
