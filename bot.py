import os
import json
import logging
from urllib.parse import quote

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import search_documents
from geography import AfghanistanGeography


# =========================================================
# تنظیمات
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# اطلاعات سدها
# =========================================================

def load_dams():

    # فایل نهایی که در پروژه ساختیم
    paths = [
        "data/dams/geodar_afghanistan_complete.json",
        "data/dams/geodar_afghanistan_final.json",
        "data/dams/geodar_afghanistan_enriched.json",
        "afghanistan_dams.json"
    ]

    for path in paths:

        if not os.path.exists(path):
            continue

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            # ساختار اصلی فایل کامل
            # {
            #   "country": "Afghanistan",
            #   "count": 7,
            #   "dams": [...]
            # }

            if isinstance(data, dict):

                dams = data.get("dams", [])

                if isinstance(dams, list):

                    print(
                        f"✅ فایل سدها بارگذاری شد: {path}"
                    )

                    print(
                        f"تعداد سدها: {len(dams)}"
                    )

                    return dams

            # اگر فایل مستقیماً لیست باشد
            if isinstance(data, list):

                print(
                    f"✅ فایل سدها بارگذاری شد: {path}"
                )

                print(
                    f"تعداد سدها: {len(data)}"
                )

                return data

        except Exception as e:

            print(
                f"⚠️ خطا در خواندن {path}: {e}"
            )

    print(
        "❌ هیچ فایل اطلاعات سدها پیدا نشد."
    )

    return []


DAMS = load_dams()


# =========================================================
# ابزارهای کمکی
# =========================================================

def get_value(dam, *keys, default="ثبت نشده"):

    for key in keys:

        value = dam.get(key)

        if value is not None and value != "":
            return value

    return default


def valid_value(value):

    if value is None:
        return False

    if str(value).strip() in (
        "",
        "-999",
        "-999.0",
        "None",
        "null"
    ):
        return False

    return True


# =========================================================
# جستجوی سدها
# =========================================================

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


# =========================================================
# متن کامل اطلاعات یک سد
# =========================================================

def dam_text(dam):

    geodar_id = get_value(
        dam,
        "geodar_id",
        "id_v11",
        "OBJECTID"
    )

    grand_id = get_value(
        dam,
        "grand_id",
        "id_grd_v13"
    )

    province = get_value(
        dam,
        "province"
    )

    district = get_value(
        dam,
        "district"
    )

    center = get_value(
        dam,
        "province_center"
    )

    distance = get_value(
        dam,
        "distance_to_province_center_km",
        "distance_to_center_km"
    )

    lat = get_value(
        dam,
        "latitude",
        "lat"
    )

    lon = get_value(
        dam,
        "longitude",
        "lon"
    )

    geo_method = get_value(
        dam,
        "geo_method",
        "geo_mtd"
    )

    qa_rank = get_value(
        dam,
        "qa_rank"
    )

    rv = get_value(
        dam,
        "reservoir_volume_mcm_v11",
        "rv_mcm_v11"
    )

    source = get_value(
        dam,
        "source",
        "harmonization_source",
        "har_src"
    )

    point_source = get_value(
        dam,
        "point_source",
        "pnt_src"
    )

    quality_control = get_value(
        dam,
        "quality_control",
        "qc"
    )

    if valid_value(distance):

        distance_text = f"{distance} km"

    else:

        distance_text = "ثبت نشده"

    if valid_value(rv):

        rv_text = f"{rv} میلیون مترمکعب"

    else:

        rv_text = "ثبت نشده"

    text = (
        f"🏗 **سد شماره {geodar_id}**\n\n"

        f"🆔 شناسه GeoDAR: `{geodar_id}`\n"
        f"🌍 شناسه GRanD: `{grand_id}`\n\n"

        f"🇦🇫 **موقعیت اداری**\n"
        f"🏛 ولایت: {province}\n"
        f"📍 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {center}\n"
        f"📏 فاصله تا مرکز ولایت: {distance_text}\n\n"

        f"🌐 **مختصات جغرافیایی**\n"
        f"عرض جغرافیایی: `{lat}`\n"
        f"طول جغرافیایی: `{lon}`\n\n"

        f"💧 **اطلاعات مخزن**\n"
        f"حجم مخزن: {rv_text}\n\n"

        f"🛰 **اطلاعات داده**\n"
        f"روش تعیین موقعیت: {geo_method}\n"
        f"رتبه کنترل کیفیت: {qa_rank}\n"
        f"منبع اصلی: {source}\n"
        f"منبع نقطه: {point_source}\n"
        f"کنترل کیفیت: {quality_control}"
    )

    return text


# =========================================================
# دکمه‌های یک سد
# =========================================================

def dam_buttons(dam):

    lat = get_value(
        dam,
        "latitude",
        "lat",
        default=None
    )

    lon = get_value(
        dam,
        "longitude",
        "lon",
        default=None
    )

    buttons = []

    if valid_value(lat) and valid_value(lon):

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                "📍 مشاهده سد روی Google Maps",
                url=maps_url
            )

        ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت به فهرست سدها",
            callback_data="dams"
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back_start"
        )

    ])

    return buttons


# =========================================================
# نمایش فهرست سدها
# =========================================================

async def show_dams(query):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.\n\n"
            "فایل GeoDAR در مسیر موردنظر موجود نیست.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_start"
                    )
                ]

            ])
        )

        return

    buttons = []

    for i, dam in enumerate(DAMS, 1):

        province = get_value(
            dam,
            "province"
        )

        district = get_value(
            dam,
            "district"
        )

        geodar_id = get_value(
            dam,
            "geodar_id",
            "id_v11",
            "OBJECTID"
        )

        buttons.append([

            InlineKeyboardButton(
                f"🏗 {i}. سد #{geodar_id} — {province}",
                callback_data=f"dam:{i - 1}"
            )

        ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    text = (
        "🏗 **سدها و بندهای افغانستان**\n\n"
        f"تعداد سدهای ثبت‌شده: **{len(DAMS)}**\n\n"
        "برای مشاهده اطلاعات کامل، یک سد را انتخاب کن:"
    )

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش اطلاعات یک سد
# =========================================================

async def show_dam(query, index):

    try:

        index = int(index)

    except ValueError:

        await query.answer(
            "شناسه سد نامعتبر است.",
            show_alert=True
        )

        return

    if index < 0 or index >= len(DAMS):

        await query.answer(
            "سد پیدا نشد.",
            show_alert=True
        )

        return

    dam = DAMS[index]

    text = dam_text(dam)

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            dam_buttons(dam)
        ),

        parse_mode="Markdown"
    )


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🇦🇫 جغرافیای افغانستان",
                callback_data="geo_provinces"
            )
        ],

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

        "🇦🇫 **دانشنامه افغانستان**\n\n"

        "یک موضوع را جستجو کن یا از منوی زیر استفاده کن.\n\n"

        "مثال:\n"
        "بند\n"
        "سد\n"
        "کابل\n"
        "مخزن",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش ولایت‌ها
# =========================================================

async def show_provinces(query):

    provinces = GEO.get_provinces()

    buttons = []

    row = []

    for province in provinces:

        button = InlineKeyboardButton(

            province["name_fa"],

            callback_data=(
                f"province:{province['id']}"
            )
        )

        row.append(button)

        if len(row) == 2:

            buttons.append(row)

            row = []

    if row:

        buttons.append(row)

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        "🇦🇫 **ولایت‌های افغانستان**\n\n"
        "یک ولایت را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش ولسوالی‌ها
# =========================================================

async def show_districts(
    query,
    province_id
):

    province = GEO.get_province(
        province_id
    )

    if not province:

        await query.answer(
            "ولایت پیدا نشد.",
            show_alert=True
        )

        return

    districts = GEO.get_districts(
        province_id
    )

    buttons = []

    row = []

    for district in districts:

        button = InlineKeyboardButton(

            district["district_name_fa"],

            callback_data=(
                f"district:{district['district_id']}"
            )
        )

        row.append(button)

        if len(row) == 2:

            buttons.append(row)

            row = []

    if row:

        buttons.append(row)

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
        )

    ])

    await query.edit_message_text(

        f"🇦🇫 ولایت {province['name_fa']}\n\n"
        f"تعداد ولسوالی‌ها: {len(districts)}\n\n"
        "یک ولسوالی را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# نمایش اطلاعات ولسوالی
# =========================================================

async def show_district(
    query,
    district_id
):

    district = GEO.get_district(
        district_id
    )

    if not district:

        await query.answer(
            "ولسوالی پیدا نشد.",
            show_alert=True
        )

        return

    lat = district.get("latitude")
    lon = district.get("longitude")

    boundary_id = district.get(
        "boundary_id",
        "ثبت نشده"
    )

    boundary_name = district.get(
        "boundary_name",
        "ثبت نشده"
    )

    text = (
        f"📍 {district['district_name_fa']}\n\n"
        f"🏛 ولایت: {district['province_fa']}\n\n"
        f"🇬🇧 نام انگلیسی: {district['district_name_en']}\n\n"
        f"🆔 شناسه ولسوالی: {district['district_id']}\n\n"
        f"📌 مرکز ولسوالی:\n"
        f"عرض: {lat}\n"
        f"طول: {lon}\n\n"
        f"🗺 مرز جغرافیایی:\n"
        f"{boundary_name}\n\n"
        f"🔗 Boundary ID:\n"
        f"{boundary_id}"
    )

    buttons = []

    if lat is not None and lon is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                "📍 مختصات جغرافیایی",
                url=maps_url
            )

        ])

    district_name = district.get(
        "district_name_en",
        ""
    )

    province_name = district.get(
        "province_en",
        ""
    )

    place_query = (
        f"{district_name}, "
        f"{province_name}, "
        "Afghanistan"
    )

    center_url = (
        "https://www.google.com/maps/search/"
        f"?api=1&query={quote(place_query)}"
    )

    buttons.append([

        InlineKeyboardButton(
            "🏙️ جستجوی مرکز ولسوالی",
            url=center_url
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولسوالی‌ها",
            callback_data=(
                f"province:{district['province_id']}"
            )
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
        )

    ])

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# مدیریت دکمه‌ها
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # -----------------------------------------------------
    # ولایت‌ها
    # -----------------------------------------------------

    if data == "geo_provinces":

        await show_provinces(query)

        return


    # -----------------------------------------------------
    # انتخاب ولایت
    # -----------------------------------------------------

    if data.startswith("province:"):

        province_id = data.split(
            ":",
            1
        )[1]

        await show_districts(
            query,
            province_id
        )

        return


    # -----------------------------------------------------
    # انتخاب ولسوالی
    # -----------------------------------------------------

    if data.startswith("district:"):

        district_id = data.split(
            ":",
            1
        )[1]

        await show_district(
            query,
            district_id
        )

        return


    # -----------------------------------------------------
    # فهرست سدها
    # -----------------------------------------------------

    if data == "dams":

        await show_dams(query)

        return


    # -----------------------------------------------------
    # انتخاب یک سد
    # -----------------------------------------------------

    if data.startswith("dam:"):

        index = data.split(
            ":",
            1
        )[1]

        await show_dam(
            query,
            index
        )

        return


    # -----------------------------------------------------
    # بازگشت به Start
    # -----------------------------------------------------

    if data == "back_start":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🇦🇫 جغرافیای افغانستان",
                    callback_data="geo_provinces"
                )
            ],

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

        await query.edit_message_text(

            "🇦🇫 **دانشنامه افغانستان**\n\n"
            "یک موضوع را انتخاب کن:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),

            parse_mode="Markdown"
        )

        return


    # -----------------------------------------------------
    # مخزن‌ها
    # -----------------------------------------------------

    if data == "reservoirs":

        await query.edit_message_text(

            "💧 **بخش مخزن‌ها**\n\n"
            "این بخش را در مرحله بعد کامل می‌کنیم.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_start"
                    )
                ]

            ]),

            parse_mode="Markdown"
        )

        return


# =========================================================
# جستجوی متنی
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:
        return


    # =====================================================
    # جستجوی سد
    # =====================================================

    dam_queries = [
        "بند",
        "سد",
        "dam",
        "dams"
    ]

    is_dam_search = any(

        word in query.lower()

        for word in dam_queries

    )


    if is_dam_search:

        if query.lower() in [
            "بند",
            "سد",
            "dam",
            "dams"
        ]:

            results = DAMS

        else:

            results = search_dams(
                query
            )


        if not results:

            await update.message.reply_text(

                "🔎 بندی با این جستجو پیدا نشد."

            )

            return


        message = (
            f"🏗 **نتایج سدها برای «{query}»**\n\n"
        )

        buttons = []


        for i, dam in enumerate(
            results[:20],
            1
        ):

            province = get_value(
                dam,
                "province"
            )

            district = get_value(
                dam,
                "district"
            )

            geodar_id = get_value(
                dam,
                "geodar_id",
                "id_v11",
                "OBJECTID"
            )

            message += (

                f"🏗 **سد #{geodar_id}**\n"
                f"🇦🇫 ولایت: {province}\n"
                f"📍 ولسوالی: {district}\n\n"

            )

            # پیدا کردن اندیس واقعی سد
            try:

                real_index = DAMS.index(dam)

                buttons.append([

                    InlineKeyboardButton(
                        f"🔎 مشاهده سد #{geodar_id}",
                        callback_data=f"dam:{real_index}"
                    )

                ])

            except ValueError:
                pass


        await update.message.reply_text(

            message[:4000],

            reply_markup=(
                InlineKeyboardMarkup(buttons)
                if buttons
                else None
            ),

            parse_mode="Markdown"
        )

        return


    # =====================================================
    # جستجوی اطلاعات قبلی
    # =====================================================

    results = search_documents(
        query
    )


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


# =========================================================
# اجرای ربات
# =========================================================

def main():

    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()

    )


    # /start
    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    # دکمه‌ها
    app.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )


    # پیام‌های متنی
    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            search

        )

    )


    print(
        "🇦🇫 Afghanistan Knowledge Bot is running..."
    )

    print(
        f"🏗 تعداد سدهای بارگذاری‌شده: {len(DAMS)}"
    )


    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
