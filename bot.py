import os
import json
import logging
from urllib.parse import quote
from threading import Thread

from flask import Flask

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
# Flask / Render
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "🇦🇫 Afghanistan Knowledge Bot is alive!"


@web_app.route("/health")
def health():
    return "OK"


def run_web():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


def keep_alive():

    thread = Thread(
        target=run_web,
        daemon=True
    )

    thread.start()


# =========================================================
# جغرافیا
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# فایل سدها
# =========================================================

DAMS_FILE = "data/dams/geodar_afghanistan_complete.json"

DAMS_PER_PAGE = 5


def load_dams():

    if not os.path.exists(DAMS_FILE):

        print("⚠️ فایل سدها پیدا نشد:")
        print(DAMS_FILE)

        return []

    try:

        with open(
            DAMS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        dams = data.get(
            "dams",
            []
        )

        print("=" * 60)
        print("✅ اطلاعات سدها بارگذاری شد")
        print(f"📄 فایل: {DAMS_FILE}")
        print(f"🏗 تعداد سدها: {len(dams)}")
        print("=" * 60)

        return dams

    except Exception as e:

        print("❌ خطا در خواندن فایل سدها:")
        print(e)

        return []


DAMS = load_dams()


# =========================================================
# تبدیل مقدار خالی
# =========================================================

def clean_value(
    value,
    default="ثبت نشده"
):

    if value is None:
        return default

    value = str(value).strip()

    if value in (
        "",
        "-999",
        "-999.0",
        "-999.00",
        "None",
        "null"
    ):
        return default

    return value


# =========================================================
# نام فارسی سد
# =========================================================

def get_dam_name_fa(dam):

    return clean_value(
        dam.get("name_fa")
        or dam.get("dam_name"),
        "سد بدون نام"
    )


# =========================================================
# نام انگلیسی سد
# =========================================================

def get_dam_name_en(dam):

    return clean_value(
        dam.get("name_en"),
        ""
    )


# =========================================================
# وضعیت سد
# =========================================================

def get_status_fa(status):

    status = clean_value(
        status,
        "ثبت نشده"
    )

    statuses = {

        "active":
            "فعال",

        "under_construction":
            "در حال ساخت",

        "proposed":
            "پیشنهادی",

        "active_partially":
            "فعال به‌صورت جزئی"
    }

    return statuses.get(
        status,
        status
    )


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
# اطلاعات کامل یک سد
# =========================================================

def dam_text(
    dam,
    number=None
):

    name_fa = get_dam_name_fa(dam)

    name_en = get_dam_name_en(dam)

    province = clean_value(
        dam.get("province")
    )

    district = clean_value(
        dam.get("district")
    )

    status = get_status_fa(
        dam.get("status")
    )

    geodar_id = clean_value(
        dam.get("geodar_id")
    )

    grand_id = clean_value(
        dam.get("grand_id")
    )

    lat = clean_value(
        dam.get("latitude")
    )

    lon = clean_value(
        dam.get("longitude")
    )

    province_center = clean_value(
        dam.get("province_center")
    )

    distance = clean_value(
        dam.get(
            "distance_to_province_center_km"
        )
    )

    geo_method = clean_value(
        dam.get("geo_method")
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    source = clean_value(
        dam.get("source")
    )

    # -----------------------------------------------------
    # مشخصات فنی
    # -----------------------------------------------------

    height = clean_value(
        dam.get("height_m")
    )

    storage = clean_value(
        dam.get(
            "storage_capacity_mcm"
        )
        or dam.get(
            "reservoir_volume_mcm_v11"
        )
    )

    power = clean_value(
        dam.get("power_capacity_mw")
    )

    irrigation = clean_value(
        dam.get("irrigation_area_ha")
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    description = clean_value(
        dam.get("description"),
        ""
    )

    location_description = clean_value(
        dam.get("location_description"),
        ""
    )

    type_description = clean_value(
        dam.get("type_description"),
        ""
    )

    history_description = clean_value(
        dam.get("history_description"),
        ""
    )

    purpose_description = clean_value(
        dam.get("purpose_description"),
        ""
    )

    importance_description = clean_value(
        dam.get("importance_description"),
        ""
    )

    power_description = clean_value(
        dam.get("power_description"),
        ""
    )

    # =====================================================
    # ساخت متن
    # =====================================================

    text = ""

    if number is not None:

        text += (
            f"🔢 <b>سد شماره {number}</b>\n\n"
        )

    text += (
        f"🏗 <b>{name_fa}</b>\n"
    )

    if name_en:

        text += (
            f"🇬🇧 {name_en}\n"
        )

    text += "\n"

    text += (
        "📍 <b>موقعیت</b>\n"
        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {province_center}\n"
        f"📏 فاصله تا مرکز ولایت: {distance} km\n"
        f"📌 وضعیت: {status}\n\n"
    )

    text += (
        "🌐 <b>مختصات جغرافیایی</b>\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"
    )

    text += (
        "🏗 <b>اطلاعات فنی</b>\n"
        f"📏 ارتفاع دیواره: {height} متر\n"
        f"💧 ظرفیت ذخیره: {storage} میلیون متر مکعب\n"
        f"⚡ ظرفیت برق: {power} مگاوات\n"
        f"🌾 مساحت آبیاری: {irrigation} هکتار\n\n"
    )

    text += (
        "🆔 <b>اطلاعات پایگاه داده</b>\n"
        f"GeoDAR ID: {geodar_id}\n"
        f"GRanD ID: {grand_id}\n\n"
    )

    text += (
        "🛰 <b>روش تعیین موقعیت</b>\n"
        f"{geo_method}\n\n"
    )

    text += (
        "✅ <b>رتبه کنترل کیفیت</b>\n"
        f"{qa_rank}\n\n"
    )

    if description:

        text += (
            "📖 <b>توضیحات</b>\n"
            f"{description}\n\n"
        )

    if location_description:

        text += (
            "📍 <b>موقعیت و محل سد</b>\n"
            f"{location_description}\n\n"
        )

    if type_description:

        text += (
            "🏗 <b>نوع سد</b>\n"
            f"{type_description}\n\n"
        )

    if history_description:

        text += (
            "📜 <b>تاریخچه و ساخت</b>\n"
            f"{history_description}\n\n"
        )

    if purpose_description:

        text += (
            "🎯 <b>کاربرد</b>\n"
            f"{purpose_description}\n\n"
        )

    if importance_description:

        text += (
            "⭐ <b>اهمیت</b>\n"
            f"{importance_description}\n\n"
        )

    if power_description:

        text += (
            "⚡ <b>برق و ظرفیت تولید</b>\n"
            f"{power_description}\n\n"
        )

    text += (
        "📚 <b>منبع</b>\n"
        f"{source}"
    )

    return text


# =========================================================
# دکمه‌های اطلاعات سد
# =========================================================

def dam_buttons(
    dam,
    dam_index,
    page
):

    buttons = []

    name_fa = get_dam_name_fa(
        dam
    )

    lat = dam.get("latitude")
    lon = dam.get("longitude")

    # -----------------------------------------------------
    # نقشه
    # -----------------------------------------------------

    if lat is not None and lon is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📍 نقشه {name_fa}",
                url=maps_url
            )

        ])

    # -----------------------------------------------------
    # قبلی / بعدی
    # -----------------------------------------------------

    navigation = []

    if dam_index > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ سد قبلی",
                callback_data=(
                    f"dam:{dam_index - 1}:{page}"
                )
            )

        )

    if dam_index < len(DAMS) - 1:

        navigation.append(

            InlineKeyboardButton(
                "سد بعدی ➡️",
                callback_data=(
                    f"dam:{dam_index + 1}:{page}"
                )
            )

        )

    if navigation:

        buttons.append(
            navigation
        )

    # -----------------------------------------------------
    # برگشت به همان صفحه فهرست
    # -----------------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🔙 فهرست سدها",
            callback_data=f"dams:{page}"
        )

    ])

    return buttons


# =========================================================
# منوی اصلی
# =========================================================

def main_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🇦🇫 جغرافیای افغانستان",
                callback_data="geo_provinces"
            )
        ],

        [
            InlineKeyboardButton(
                "🏗 بندها و سدها",
                callback_data="dams:0"
            )
        ],

        [
            InlineKeyboardButton(
                "💧 مخزن‌ها",
                callback_data="reservoirs"
            )
        ]

    ])


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🇦🇫 <b>دانشنامه افغانستان</b>\n\n"
        "یک موضوع را انتخاب کن یا جستجو کن.\n\n"
        "مثال:\n"
        "بند\n"
        "سد\n"
        "کابل\n"
        "مخزن",

        reply_markup=main_keyboard(),

        parse_mode="HTML"
    )


# =========================================================
# نمایش فهرست سدها
# =========================================================

async def show_dams(
    query,
    page=0
):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.",

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

    # -----------------------------------------------------
    # محاسبه صفحات
    # -----------------------------------------------------

    total = len(DAMS)

    total_pages = (
        total + DAMS_PER_PAGE - 1
    ) // DAMS_PER_PAGE

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start_index = (
        page * DAMS_PER_PAGE
    )

    end_index = min(
        start_index + DAMS_PER_PAGE,
        total
    )

    page_dams = DAMS[
        start_index:end_index
    ]

    # -----------------------------------------------------
    # متن
    # -----------------------------------------------------

    message = (
        "🏗 <b>بندها و سدهای افغانستان</b>\n\n"
        f"📊 تعداد سدهای ثبت‌شده: {total}\n"
        f"📄 صفحه {page + 1} از {total_pages}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    # -----------------------------------------------------
    # سدهای این صفحه
    # -----------------------------------------------------

    for local_index, dam in enumerate(
        page_dams
    ):

        real_index = (
            start_index + local_index
        )

        name_fa = get_dam_name_fa(
            dam
        )

        name_en = get_dam_name_en(
            dam
        )

        province = clean_value(
            dam.get("province")
        )

        district = clean_value(
            dam.get("district")
        )

        message += (
            f"🔢 <b>سد شماره {real_index + 1}</b>\n"
            f"🏗 {name_fa}\n"
        )

        if name_en:

            message += (
                f"🇬🇧 {name_en}\n"
            )

        message += (
            f"🇦🇫 ولایت: {province}\n"
            f"🏘 ولسوالی: {district}\n\n"
        )

        # اطلاعات
        buttons.append([

            InlineKeyboardButton(
                f"📖 اطلاعات {name_fa}",
                callback_data=(
                    f"dam:{real_index}:{page}"
                )
            )

        ])

        # نقشه
        lat = dam.get("latitude")
        lon = dam.get("longitude")

        if lat is not None and lon is not None:

            maps_url = (
                "https://www.google.com/maps/search/"
                f"?api=1&query={lat},{lon}"
            )

            buttons.append([

                InlineKeyboardButton(
                    f"📍 نقشه {name_fa}",
                    url=maps_url
                )

            ])

    # =====================================================
    # دکمه‌های صفحات
    # =====================================================

    navigation = []

    if page > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=(
                    f"dams:{page - 1}"
                )
            )

        )

    if page < total_pages - 1:

        navigation.append(

            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=(
                    f"dams:{page + 1}"
                )
            )

        )

    if navigation:

        buttons.append(
            navigation
        )

    # -----------------------------------------------------
    # بازگشت
    # -----------------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        message,

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="HTML"
    )


# =========================================================
# نمایش اطلاعات یک سد
# =========================================================

async def show_single_dam(
    query,
    dam_index,
    page=0
):

    try:

        index = int(
            dam_index
        )

        page = int(
            page
        )

    except ValueError:

        await query.answer(
            "شناسه سد نامعتبر است.",
            show_alert=True
        )

        return

    # -----------------------------------------------------
    # بررسی اندیس
    # -----------------------------------------------------

    if index < 0 or index >= len(DAMS):

        await query.answer(
            "سد پیدا نشد.",
            show_alert=True
        )

        return

    dam = DAMS[index]

    name_fa = get_dam_name_fa(
        dam
    )

    print(
        f"📖 نمایش اطلاعات سد #{index + 1}: "
        f"{name_fa}"
    )

    text = dam_text(
        dam,
        index + 1
    )

    buttons = dam_buttons(
        dam,
        index,
        page
    )

    # -----------------------------------------------------
    # محدودیت تلگرام
    # -----------------------------------------------------

    if len(text) > 4000:

        text = text[:3950] + "\n\n..."

    try:

        await query.edit_message_text(

            text,

            reply_markup=InlineKeyboardMarkup(
                buttons
            ),

            parse_mode="HTML"
        )

    except Exception as e:

        print(
            "❌ خطا در نمایش اطلاعات سد:"
        )

        print(
            f"سد #{index + 1} - {name_fa}"
        )

        print(e)

        await query.answer(
            "در نمایش اطلاعات این سد خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# جستجوی متنی سدها
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_query = (
        update.message.text.strip()
    )

    if not user_query:
        return

    query_lower = (
        user_query.lower()
    )

    dam_keywords = [
        "بند",
        "سد",
        "dam",
        "dams"
    ]

    is_dam_search = any(
        word in query_lower
        for word in dam_keywords
    )

    if is_dam_search:

        results = search_dams(
            user_query
        )

        if query_lower in (
            "بند",
            "سد",
            "dam",
            "dams"
        ):

            results = DAMS

        if not results:

            await update.message.reply_text(
                "🔎 بندی با این جستجو پیدا نشد."
            )

            return

        message = (
            f"🏗 <b>نتایج سدها برای "
            f"«{user_query}»</b>\n\n"
        )

        buttons = []

        for dam in results[:20]:

            name_fa = get_dam_name_fa(
                dam
            )

            name_en = get_dam_name_en(
                dam
            )

            province = clean_value(
                dam.get("province")
            )

            district = clean_value(
                dam.get("district")
            )

            try:

                real_index = DAMS.index(
                    dam
                )

            except ValueError:

                continue

            message += (
                f"🏗 <b>{name_fa}</b>\n"
            )

            if name_en:

                message += (
                    f"🇬🇧 {name_en}\n"
                )

            message += (
                f"🇦🇫 ولایت: {province}\n"
                f"🏘 ولسوالی: {district}\n\n"
            )

            buttons.append([

                InlineKeyboardButton(
                    f"📖 اطلاعات {name_fa}",
                    callback_data=(
                        f"dam:{real_index}:0"
                    )
                )

            ])

            lat = dam.get("latitude")
            lon = dam.get("longitude")

            if lat is not None and lon is not None:

                maps_url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"
                )

                buttons.append([

                    InlineKeyboardButton(
                        f"📍 نقشه {name_fa}",
                        url=maps_url
                    )

                ])

        await update.message.reply_text(

            message[:4000],

            reply_markup=InlineKeyboardMarkup(
                buttons
            ),

            parse_mode="HTML"
        )

        return

    # =====================================================
    # جستجوی عمومی دیتابیس
    # =====================================================

    results = search_documents(
        user_query
    )

    if not results:

        await update.message.reply_text(

            f"🔎 برای «{user_query}» "
            "چیزی پیدا نشد."

        )

        return

    message = (
        f"🔎 <b>نتایج برای "
        f"«{user_query}»</b>\n\n"
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

        message[:4000],

        parse_mode="HTML"
    )


# =========================================================
# دکمه‌های جغرافیا
# =========================================================

async def show_provinces(query):

    provinces = GEO.get_provinces()

    buttons = []

    row = []

    for province in provinces:

        row.append(

            InlineKeyboardButton(
                province["name_fa"],
                callback_data=(
                    f"province:{province['id']}"
                )
            )

        )

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

        "🇦🇫 <b>ولایت‌های افغانستان</b>\n\n"
        "یک ولایت را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="HTML"
    )


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

        row.append(

            InlineKeyboardButton(

                district[
                    "district_name_fa"
                ],

                callback_data=(
                    f"district:"
                    f"{district['district_id']}"
                )

            )

        )

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
        f"تعداد ولسوالی‌ها: "
        f"{len(districts)}\n\n"
        "یک ولسوالی را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


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

    text = (
        f"📍 {district['district_name_fa']}\n\n"
        f"🏛 ولایت: {district['province_fa']}\n\n"
        f"🇬🇧 نام انگلیسی: "
        f"{district['district_name_en']}\n\n"
        f"🆔 شناسه ولسوالی: "
        f"{district['district_id']}\n\n"
        f"📌 مرکز ولسوالی:\n"
        f"عرض: {lat}\n"
        f"طول: {lon}\n"
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
                f"province:"
                f"{district['province_id']}"
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
# مدیریت تمام دکمه‌ها
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    data = query.data

    print(
        f"🔘 Callback: {data}"
    )

    await query.answer()

    # -----------------------------------------------------
    # جغرافیا
    # -----------------------------------------------------

    if data == "geo_provinces":

        await show_provinces(
            query
        )

        return

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

        await show_dams(
            query,
            0
        )

        return

    if data.startswith("dams:"):

        try:

            page = int(
                data.split(
                    ":",
                    1
                )[1]
            )

        except ValueError:

            page = 0

        await show_dams(
            query,
            page
        )

        return

    # -----------------------------------------------------
    # اطلاعات سد
    # -----------------------------------------------------

    if data.startswith("dam:"):

        parts = data.split(":")

        try:

            dam_index = int(
                parts[1]
            )

        except (
            ValueError,
            IndexError
        ):

            await query.answer(
                "شناسه سد نامعتبر است.",
                show_alert=True
            )

            return

        # صفحه فهرست
        try:

            page = int(
                parts[2]
            )

        except (
            ValueError,
            IndexError
        ):

            page = (
                dam_index //
                DAMS_PER_PAGE
            )

        await show_single_dam(
            query,
            dam_index,
            page
        )

        return

    # -----------------------------------------------------
    # مخزن‌ها
    # -----------------------------------------------------

    if data == "reservoirs":

        await query.edit_message_text(

            "💧 <b>بخش مخزن‌ها</b>\n\n"
            "این بخش را در مرحله بعد کامل می‌کنیم.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_start"
                    )
                ]

            ]),

            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # بازگشت اصلی
    # -----------------------------------------------------

    if data == "back_start":

        await query.edit_message_text(

            "🇦🇫 <b>دانشنامه افغانستان</b>\n\n"
            "یک موضوع را انتخاب کن:",

            reply_markup=main_keyboard(),

            parse_mode="HTML"
        )

        return


# =========================================================
# اجرای ربات
# =========================================================

def main():

    print("=" * 60)
    print("🇦🇫 Afghanistan Knowledge Bot")
    print("✅ ربات در حال اجرا است...")
    print(
        f"🏗 تعداد سدهای بارگذاری‌شده: "
        f"{len(DAMS)}"
    )
    print("=" * 60)

    # -----------------------------------------------------
    # Render
    # -----------------------------------------------------

    keep_alive()

    print(
        "🌐 Render Keep-Alive فعال شد."
    )

    # -----------------------------------------------------
    # Telegram
    # -----------------------------------------------------

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
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            search
        )
    )

    print(
        "🤖 Telegram polling شروع شد..."
    )

    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
