import os
import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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


# =====================================
# اطلاعات بندهای افغانستان
# =====================================

def load_dams():

    path = "afghanistan_dams.json"

    if not os.path.exists(path):

        print("⚠️ afghanistan_dams.json پیدا نشد.")

        return []

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


DAMS = load_dams()


# =====================================
# جستجوی بندها
# =====================================

def search_dams(query):

    query = query.lower().strip()

    results = []

    for dam in DAMS:

        text = " ".join(
            str(value)
            for value in dam.values()
        ).lower()

        if query in text:

            results.append(dam)

    return results


# =====================================
# /start
# =====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🏗 بندها و سدها",
                callback_data="dams"
            )
        ],

        [
            InlineKeyboardButton(
                "💧 مخزن‌ها",
                callback_data="reservoirs"
            )
        ]

    ]

    await update.message.reply_text(

        "🇦🇫 دانشنامه افغانستان\n\n"

        "یک موضوع را جستجو کن.\n\n"

        "مثال:\n"
        "بند\n"
        "سد\n"
        "کابل\n"
        "مخزن",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =====================================
# نمایش بند
# =====================================

def dam_text(dam):

    object_id = dam.get(
        "OBJECTID",
        "نامشخص"
    )

    lat = dam.get(
        "lat",
        ""
    )

    lon = dam.get(
        "lon",
        ""
    )

    geo_method = dam.get(
        "geo_mtd",
        ""
    )

    qa_rank = dam.get(
        "qa_rank",
        ""
    )

    rv = dam.get(
        "rv_mcm_v11",
        ""
    )

    source = dam.get(
        "har_src",
        ""
    )


    text = (

        f"🏗 بند GeoDAR #{object_id}\n\n"

        f"📍 موقعیت:\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"

        f"🛰 روش تعیین موقعیت:\n"
        f"{geo_method or 'ثبت نشده'}\n\n"

        f"✅ رتبه کنترل کیفیت:\n"
        f"{qa_rank or 'ثبت نشده'}\n\n"

        f"💧 حجم مخزن:\n"
        f"{rv if rv not in ('', '-999.0', '-999') else 'ثبت نشده'}\n\n"

        f"📚 منبع:\n"
        f"{source or 'ثبت نشده'}"
    )

    return text


# =====================================
# جستجوی متن
# =====================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return


    # جستجوی بند
    dam_queries = [
        "بند",
        "سد",
        "dam"
    ]


    is_dam_search = any(
        word in query.lower()
        for word in dam_queries
    )


    if is_dam_search:

        results = search_dams(query)

        # اگر خود کلمه بند یا سد بود،
        # همه بندها نمایش داده شوند
        if query in ["بند", "سد", "dam"]:

            results = DAMS


        if not results:

            await update.message.reply_text(
                "🔎 بندی با این جستجو پیدا نشد."
            )

            return


        message = (
            f"🏗 نتایج بندها برای «{query}»\n\n"
        )

        buttons = []


        for dam in results[:20]:

            message += (
                dam_text(dam)
                + "\n"
                + "────────────\n\n"
            )


            lat = dam.get("lat")
            lon = dam.get("lon")


            if lat and lon:

                url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"
                )

                buttons.append(

                    [
                        InlineKeyboardButton(
                            "📍 مشاهده روی Google Maps",
                            url=url
                        )
                    ]
                )


            if len(message) > 3500:

                message += "..."

                break


        await update.message.reply_text(

            message,

            reply_markup=(
                InlineKeyboardMarkup(buttons)
                if buttons
                else None
            )
        )

        return


    # ================================
    # جستجوی اطلاعات قبلی
    # ================================

    results = search_documents(query)


    if not results:

        await update.message.reply_text(

            f"🔎 برای «{query}» چیزی پیدا نشد."
        )

        return


    message = (
        f"🔎 نتایج برای «{query}»\n\n"
    )


    for i, result in enumerate(
        results,
        1
    ):

        _, title, category, content = result

        message += (

            f"📌 {i}. {title}\n"
            f"📂 {category}\n"
            f"📝 {content[:500]}\n\n"
        )


    await update.message.reply_text(
        message[:4000]
    )


# =====================================
# اجرای ربات
# =====================================

def main():

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
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print(
        "🇦🇫 Afghanistan Knowledge Bot is running..."
    )


    app.run_polling()


if __name__ == "__main__":

    main()
