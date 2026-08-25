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

    print(f"🏗 {count} رکورد GeoDAR وارد شد.")


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

    for i, result in enumerate(results, 1):

        # نتیجه را باز می‌کنیم
        _, title, category, content = result

        message += (
            f"📌 {i}. {title}\n"
            f"📂 دسته: {category}\n"
            f"📝 {content[:600]}\n\n"
        )

        if len(message) > 3500:
            message += "..."
            break

    await update.message.reply_text(message)


def main():

    load_test_data()
    load_reservoirs()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )

    print("🇦🇫 Afghanistan Knowledge Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
