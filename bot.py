import os
import json
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from database import (
    search_documents,
    add_document
)


logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN تنظیم نشده است."
    )


# ==================================
# داده‌های آزمایشی
# ==================================

TEST_DATA = [

    (
        "کابل",
        "جغرافیا",
        "کابل پایتخت افغانستان است.",
        "کابل افغانستان پایتخت شهر"
    ),

    (
        "غزنی",
        "جغرافیا",
        "غزنی یکی از شهرهای تاریخی افغانستان است.",
        "غزنی افغانستان شهر تاریخی"
    ),

    (
        "هرات",
        "جغرافیا",
        "هرات یکی از شهرهای مهم تاریخی افغانستان است.",
        "هرات افغانستان شهر تاریخی"
    ),

    (
        "بند کجکی",
        "بندها و مخازن",
        "بند کجکی در ولایت هلمند افغانستان قرار دارد.",
        "بند سد مخزن کجکی هلمند افغانستان"
    ),

    (
        "احمدشاه ابدالی",
        "شاهان و فرمانروایان",
        "احمدشاه ابدالی بنیان‌گذار امپراتوری درانی بود.",
        "احمدشاه ابدالی شاه درانی تاریخ افغانستان"
    )
]


def load_test_data():

    for (
        title,
        category,
        content,
        keywords
    ) in TEST_DATA:

        if not search_documents(title):

            add_document(
                title,
                category,
                content,
                keywords
            )


# ==================================
# وارد کردن GeoDAR
# ==================================

def load_reservoirs():

    if not os.path.exists(
        "reservoirs.json"
    ):

        print(
            "reservoirs.json پیدا نشد."
        )

        return


    with open(
        "reservoirs.json",
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)


    count = 0


    for item in data:

        title = item["title"]

        # کلیدواژه‌های مربوط به بند و مخزن
        keywords = (
            "بند سد مخزن "
            "reservoir dam "
            "GeoDAR افغانستان"
        )


        if not search_documents(title):

            add_document(
                title,
                item["category"],
                item["content"],
                keywords
            )

            count += 1


    print(
        f"🏗 {count} رکورد GeoDAR وارد شد."
    )


# ==================================
# دسته‌بندی
# ==================================

CATEGORIES = {

    "جغرافیا": "جغرافیا",

    "بند": "بندها و مخازن",

    "سد": "بندها و مخازن",

    "مخزن": "بندها و مخازن",

    "کوه": "کوه‌ها",

    "رود": "رودخانه‌ها",

    "رودخانه": "رودخانه‌ها",

    "شهر": "شهرها و روستاها",

    "شاه": "شاهان و فرمانروایان",

    "شاهان": "شاهان و فرمانروایان",

    "جنگ": "جنگ‌ها",

    "تاریخ": "تاریخ",

    "حکومت": "حکومت‌ها"
}


# ==================================
# /start
# ==================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🗺 جغرافیا",
                callback_data="cat_جغرافیا"
            )
        ],

        [
            InlineKeyboardButton(
                "🏗 بندها و مخازن",
                callback_data="cat_بندها و مخازن"
            )
        ],

        [
            InlineKeyboardButton(
                "👑 شاهان",
                callback_data="cat_شاهان و فرمانروایان"
            )
        ],

        [
            InlineKeyboardButton(
                "📜 تاریخ",
                callback_data="cat_تاریخ"
            )
        ]
    ]


    await update.message.reply_text(

        "🇦🇫 دانشنامه افغانستان\n\n"

        "🔎 برای جستجو یک کلمه یا موضوع بفرست.\n\n"

        "مثال:\n"
        "بند\n"
        "کابل\n"
        "شاه\n"
        "جنگ\n"
        "تاریخ\n\n"

        "یا یکی از دسته‌ها را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================
# جستجو
# ==================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return


    # بررسی دسته
    category = CATEGORIES.get(
        query.lower()
    )


    results = search_documents(
        query,
        category
    )


    if not results:

        await update.message.reply_text(

            f"🔎 برای «{query}» چیزی پیدا نشد.\n\n"

            "سعی کن با یک کلمه ساده‌تر جستجو کنی."
        )

        return


    message = (
        f"🔎 نتایج برای «{query}»\n\n"
    )


    buttons = []


    for i, result in enumerate(
        results,
        1
    ):

        _, title, category_name, content = result


        message += (

            f"📌 {i}. {title}\n"
            f"📂 {category_name}\n"
            f"📝 {content[:450]}\n\n"
        )


        # استخراج مختصات
        lat = None
        lon = None


        for line in content.splitlines():

            if line.startswith(
                "عرض جغرافیایی:"
            ):

                lat = line.split(
                    ":",
                    1
                )[1].strip()


            elif line.startswith(
                "طول جغرافیایی:"
            ):

                lon = line.split(
                    ":",
                    1
                )[1].strip()


        # Google Maps
        if lat and lon:

            maps_url = (
                "https://www.google.com/maps/search/"
                f"?api=1&query={lat},{lon}"
            )


            buttons.append(

                [
                    InlineKeyboardButton(
                        "📍 مشاهده روی Google Maps",
                        url=maps_url
                    )
                ]
            )


        if len(message) > 3500:

            message += "..."

            break


    keyboard = None


    if buttons:

        keyboard = InlineKeyboardMarkup(
            buttons
        )


    await update.message.reply_text(

        message,

        reply_markup=keyboard
    )


# ==================================
# اجرا
# ==================================

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
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            search
        )
    )


    print(
        "🇦🇫 Afghanistan Knowledge Bot is running..."
    )


    app.run_polling()


if __name__ == "__main__":

    main()
