import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import search_documents, add_document


# =============================
# تنظیمات لاگ
# =============================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =============================
# دریافت توکن از Render
# =============================

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("BOT_TOKEN exists:", bool(BOT_TOKEN))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =============================
# داده‌های آزمایشی
# =============================

TEST_DATA = [
    (
        "کابل",
        "جغرافیا",
        "کابل پایتخت افغانستان است و در بخش شرقی کشور قرار دارد."
    ),

    (
        "غزنی",
        "جغرافیا",
        "غزنی یکی از شهرهای تاریخی افغانستان است."
    ),

    (
        "هرات",
        "جغرافیا",
        "هرات یکی از شهرهای مهم تاریخی و فرهنگی افغانستان است."
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


# =============================
# وارد کردن داده‌های آزمایشی
# =============================

def load_test_data():

    for title, category, content in TEST_DATA:

        add_document(
            title,
            category,
            content
        )

    print("🇦🇫 داده‌های آزمایشی وارد دیتابیس شدند.")


# =============================
# دستور /start
# =============================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🇦🇫 به ربات دانشنامه افغانستان خوش آمدید!\n\n"

        "🔎 برای جستجو، موضوع موردنظر را ارسال کن.\n\n"

        "مثال:\n"
        "• کابل\n"
        "• غزنی\n"
        "• هرات\n"
        "• بند کجکی\n"
        "• احمدشاه ابدالی\n\n"

        "📚 فعلاً نسخه آزمایشی دانشنامه فعال است."
    )


# =============================
# جستجو
# =============================

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
            f"🔎 برای «{query}» چیزی پیدا نشد.\n\n"
            "📚 منابع بیشتری به‌زودی اضافه می‌شوند."
        )

        return


    message = (
        f"🔎 نتایج جستجو برای:\n"
        f"«{query}»\n\n"
    )


    for i, (_, title, category, content) in enumerate(
        results,
        start=1
    ):

        short_content = content[:700]

        message += (
            f"📌 {i}. {title}\n"
            f"📂 دسته: {category}\n"
            f"📝 {short_content}\n\n"
        )

        # محدودیت پیام تلگرام
        if len(message) > 3500:

            message += "...\n"

            break


    await update.message.reply_text(
        message
    )


# =============================
# اجرای ربات
# =============================

def main():

    # وارد کردن داده‌های آزمایشی
    load_test_data()


    # ساخت برنامه
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # دستور Start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    # جستجوی متن
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print(
        "🇦🇫 Afghanistan Knowledge Bot is running..."
    )


    # اجرای ربات
    app.run_polling()


# =============================
# شروع برنامه
# =============================

if __name__ == "__main__":
    main()
