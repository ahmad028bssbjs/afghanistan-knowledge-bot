import os
import json
import logging
from urllib.parse import quote
from threading import Thread
from html import escape

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
# Render Keep Alive
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
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# فایل سدها
# =========================================================

DAMS_FILE = "data/dams/geodar_afghanistan_complete.json"

DAMS = []


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
        print(f"📁 فایل: {DAMS_FILE}")
        print(f"🏗 تعداد سدها: {len(dams)}")
        print("=" * 60)

        return dams

    except Exception as e:

        print("❌ خطا در خواندن فایل سدها:")
        print(e)

        return []


DAMS = load_dams()


# =========================================================
# تنظیمات صفحه‌بندی
# =========================================================

DAMS_PER_PAGE = 5


def total_pages(items):

    if not items:
        return 1

    return (
        len(items) + DAMS_PER_PAGE - 1
    ) // DAMS_PER_PAGE


def get_page_items(
    items,
    page
):

    start = page * DAMS_PER_PAGE

    end = start + DAMS_PER_PAGE

    return items[start:end]


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
        "null",
        "nan"
    ):
        return default

    return value


# =========================================================
# نام فارسی سد
# =========================================================

def get_name_fa(dam):

    return clean_value(
        dam.get("name_fa"),
        clean_value(
            dam.get("dam_name"),
            "سد بدون نام"
        )
    )


# =========================================================
# نام انگلیسی سد
# =========================================================

def get_name_en(dam):

    return clean_value(
        dam.get("name_en"),
        clean_value(
            dam.get("dam_name"),
            "Unnamed Dam"
        )
    )


# =========================================================
# وضعیت سد
# =========================================================

def get_status_text(dam):

    status = clean_value(
        dam.get("status")
    )

    status_map = {

        "active":
            "فعال",

        "under_construction":
            "در حال ساخت",

        "proposed":
            "پیشنهادی",

        "active_partially":
            "فعال / نیمه‌فعال"

    }

    return status_map.get(
        status,
        status
    )


# =========================================================
# جستجوی سدها
# =========================================================

def search_dams(query):

    query = query.lower().strip()

    results = []

    for index, dam in enumerate(DAMS):

        text = " ".join(
            str(value)
            for value in dam.values()
        ).lower()

        if query in text:

            results.append(index)

    return results


# =========================================================
# متن یک سد
# =========================================================

def dam_text(
    dam,
    number=None
):

    dam_name_fa = get_name_fa(dam)

    dam_name_en = get_name_en(dam)

    geodar_id = clean_value(
        dam.get("geodar_id")
    )

    district = clean_value(
        dam.get("district")
    )

    province = clean_value(
        dam.get("province")
    )

    province_center = clean_value(
        dam.get("province_center")
    )

    distance = clean_value(
        dam.get(
            "distance_to_province_center_km"
        )
    )

    lat = clean_value(
        dam.get("latitude")
    )

    lon = clean_value(
        dam.get("longitude")
    )

    grand_id = clean_value(
        dam.get("grand_id")
    )

    geo_method = clean_value(
        dam.get("geo_method")
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    reservoir = clean_value(
        dam.get("reservoir_volume_mcm_v11")
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    height = clean_value(
        dam.get("height_m")
    )

    storage = clean_value(
        dam.get("storage_capacity_mcm")
    )

    power = clean_value(
        dam.get("power_capacity_mw")
    )

    irrigation = clean_value(
        dam.get("irrigation_area_ha")
    )

    status = get_status_text(dam)

    source = clean_value(
        dam.get("source")
    )

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

    text = ""

    if number is not None:

        text += (
            f"🔢 <b>سد شماره {number}</b>\n\n"
        )

    text += (
        f"🏗 <b>{escape(dam_name_fa)}</b>\n"
        f"🇬🇧 {escape(dam_name_en)}\n\n"
    )

    # -----------------------------------------------------
    # وضعیت
    # -----------------------------------------------------

    text += (
        "📊 <b>وضعیت</b>\n"
        f"{escape(status)}\n\n"
    )

    # -----------------------------------------------------
    # موقعیت
    # -----------------------------------------------------

    text += (
        "📍 <b>موقعیت</b>\n"
        f"🇦🇫 ولایت: {escape(province)}\n"
        f"🏘 ولسوالی: {escape(district)}\n"
        f"🏙 مرکز ولایت: {escape(province_center)}\n"
        f"📏 فاصله تا مرکز ولایت: {escape(distance)} km\n\n"
    )

    # -----------------------------------------------------
    # مختصات
    # -----------------------------------------------------

    text += (
        "🌐 <b>مختصات</b>\n"
        f"عرض جغرافیایی: {escape(lat)}\n"
        f"طول جغرافیایی: {escape(lon)}\n\n"
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    text += "🏗 <b>اطلاعات فنی</b>\n"

    text += (
        f"📏 ارتفاع دیواره: "
        f"{escape(height)} متر\n"
    )

    text += (
        f"💧 ظرفیت ذخیره: "
        f"{escape(storage)} میلیون مترمکعب\n"
    )

    text += (
        f"⚡ ظرفیت برق: "
        f"{escape(power)} مگاوات\n"
    )

    text += (
        f"🌾 مساحت آبیاری: "
        f"{escape(irrigation)} هکتار\n\n"
    )

    # -----------------------------------------------------
    # GeoDAR
    # -----------------------------------------------------

    text += (
        "🆔 <b>اطلاعات پایگاه داده</b>\n"
        f"GeoDAR ID: {escape(geodar_id)}\n"
        f"GRanD ID: {escape(grand_id)}\n\n"
    )

    # -----------------------------------------------------
    # روش تعیین موقعیت
    # -----------------------------------------------------

    text += (
        "🛰 <b>روش تعیین موقعیت</b>\n"
        f"{escape(geo_method)}\n\n"
    )

    # -----------------------------------------------------
    # کنترل کیفیت
    # -----------------------------------------------------

    text += (
        "✅ <b>رتبه کنترل کیفیت</b>\n"
        f"{escape(qa_rank)}\n\n"
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    if description:

        text += (
            "📖 <b>توضیحات</b>\n"
            f"{escape(description)}\n\n"
        )

    if location_description:

        text += (
            "📍 <b>موقعیت و محل سد</b>\n"
            f"{escape(location_description)}\n\n"
        )

    if type_description:

        text += (
            "🏗 <b>نوع سد</b>\n"
            f"{escape(type_description)}\n\n"
        )

    if history_description:

        text += (
            "📜 <b>تاریخچه و ساخت</b>\n"
            f"{escape(history_description)}\n\n"
        )

    if purpose_description:

        text += (
            "🎯 <b>کاربرد</b>\n"
            f"{escape(purpose_description)}\n\n"
        )

    if importance_description:

        text += (
            "⭐ <b>اهمیت</b>\n"
            f"{escape(importance_description)}\n\n"
        )

    if power_description:

        text += (
            "⚡ <b>برق و ظرفیت تولید</b>\n"
            f"{escape(power_description)}\n\n"
        )

    # -----------------------------------------------------
    # منبع
    # -----------------------------------------------------

    text += (
        "📚 <b>منبع</b>\n"
        f"{escape(source)}"
    )

    return text


# =========================================================
# دکمه‌های صفحه اطلاعات سد
# =========================================================

def dam_buttons(
    dam,
    index
):

    buttons = []

    dam_name = get_name_fa(dam)

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
                f"📍 نقشه {dam_name}",
                url=maps_url
            )

        ])

    # -----------------------------------------------------
    # قبلی / بعدی
    # -----------------------------------------------------

    navigation = []

    if index > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ سد قبلی",
                callback_data=f"dam:{index - 1}"
            )

        )

    if index < len(DAMS) - 1:

        navigation.append(

            InlineKeyboardButton(
                "سد بعدی ➡️",
                callback_data=f"dam:{index + 1}"
            )

        )

    if navigation:

        buttons.append(navigation)

    # -----------------------------------------------------
    # فهرست
    # -----------------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "📋 فهرست سدها",
            callback_data="dams:0"
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
# نمایش ولایت‌ها
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

        f"🇦🇫 <b>ولایت {escape(province['name_fa'])}</b>\n\n"
        f"تعداد ولسوالی‌ها: "
        f"{len(districts)}\n\n"
        "یک ولسوالی را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="HTML"
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
        f"📍 <b>{escape(district['district_name_fa'])}</b>\n\n"
        f"🏛 ولایت: "
        f"{escape(district['province_fa'])}\n\n"
        f"🇬🇧 نام انگلیسی: "
        f"{escape(district['district_name_en'])}\n\n"
        f"🆔 شناسه ولسوالی: "
        f"{escape(str(district['district_id']))}\n\n"
        f"📌 <b>مرکز ولسوالی</b>\n"
        f"عرض: {escape(str(lat))}\n"
        f"طول: {escape(str(lon))}\n\n"
        f"🗺 <b>مرز جغرافیایی</b>\n"
        f"{escape(str(boundary_name))}\n\n"
        f"🔗 <b>Boundary ID</b>\n"
        f"{escape(str(boundary_id))}"
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
        ),

        parse_mode="HTML"
    )


# =========================================================
# ساخت صفحه فهرست سدها
# =========================================================

def build_dams_page(
    page
):

    total = len(DAMS)

    pages = total_pages(DAMS)

    if page < 0:

        page = 0

    if page >= pages:

        page = pages - 1

    start = page * DAMS_PER_PAGE

    end = min(
        start + DAMS_PER_PAGE,
        total
    )

    current = DAMS[start:end]

    message = (
        "🏗 <b>بندها و سدهای افغانستان</b>\n\n"
        f"📊 تعداد سدهای ثبت‌شده: {total}\n"
        f"📄 صفحه {page + 1} از {pages}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    for local_index, dam in enumerate(
        current
    ):

        real_index = start + local_index

        name_fa = get_name_fa(dam)

        name_en = get_name_en(dam)

        province = clean_value(
            dam.get("province")
        )

        district = clean_value(
            dam.get("district")
        )

        message += (
            f"🔢 <b>سد شماره {real_index + 1}</b>\n"
            f"🏗 {escape(name_fa)}\n"
            f"🇬🇧 {escape(name_en)}\n"
            f"🇦🇫 ولایت: {escape(province)}\n"
            f"🏘 ولسوالی: {escape(district)}\n\n"
        )

        # فقط یک دکمه برای هر سد
        buttons.append([

            InlineKeyboardButton(
                f"📖 اطلاعات {name_fa}",
                callback_data=f"dam:{real_index}"
            )

        ])

    # -----------------------------------------------------
    # دکمه‌های صفحه
    # -----------------------------------------------------

    navigation = []

    if page > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"dams:{page - 1}"
            )

        )

    if page < pages - 1:

        navigation.append(

            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=f"dams:{page + 1}"
            )

        )

    if navigation:

        buttons.append(navigation)

    buttons.append([

        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back_start"
        )

    ])

    return (
        message,
        InlineKeyboardMarkup(buttons)
    )


# =========================================================
# نمایش سدها با صفحه‌بندی
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

    message, keyboard = build_dams_page(
        page
    )

    await query.edit_message_text(

        message,

        reply_markup=keyboard,

        parse_mode="HTML"
    )


# =========================================================
# نمایش اطلاعات یک سد
# =========================================================

async def show_single_dam(
    query,
    dam_index
):

    try:

        index = int(dam_index)

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

    text = dam_text(
        dam,
        index + 1
    )

    buttons = dam_buttons(
        dam,
        index
    )

    await query.edit_message_text(

        text[:4000],

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="HTML"
    )


# =========================================================
# نمایش صفحه جستجوی سدها
# =========================================================

def build_search_page(
    result_indexes,
    page,
    search_query
):

    total = len(result_indexes)

    pages = total_pages(
        result_indexes
    )

    if page < 0:

        page = 0

    if page >= pages:

        page = pages - 1

    current_indexes = get_page_items(
        result_indexes,
        page
    )

    message = (
        f"🏗 <b>نتایج سدها برای "
        f"«{escape(search_query)}»</b>\n\n"
        f"📊 تعداد نتایج: {total}\n"
        f"📄 صفحه {page + 1} از {pages}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    for dam_index in current_indexes:

        dam = DAMS[dam_index]

        name_fa = get_name_fa(dam)

        name_en = get_name_en(dam)

        province = clean_value(
            dam.get("province")
        )

        district = clean_value(
            dam.get("district")
        )

        message += (
            f"🏗 <b>{escape(name_fa)}</b>\n"
            f"🇬🇧 {escape(name_en)}\n"
            f"🇦🇫 ولایت: {escape(province)}\n"
            f"🏘 ولسوالی: {escape(district)}\n\n"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📖 اطلاعات {name_fa}",
                callback_data=f"dam:{dam_index}"
            )

        ])

    # -----------------------------------------------------
    # قبلی / بعدی
    # -----------------------------------------------------

    navigation = []

    if page > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"dsearch:{page - 1}"
            )

        )

    if page < pages - 1:

        navigation.append(

            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=f"dsearch:{page + 1}"
            )

        )

    if navigation:

        buttons.append(navigation)

    buttons.append([

        InlineKeyboardButton(
            "🏗 همه سدها",
            callback_data="dams:0"
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back_start"
        )

    ])

    return (
        message,
        InlineKeyboardMarkup(buttons)
    )


# =========================================================
# نمایش نتایج جستجوی سد
# =========================================================

async def show_dam_search_page(
    query,
    context,
    page=0
):

    result_indexes = context.user_data.get(
        "dam_search_indexes",
        []
    )

    search_query = context.user_data.get(
        "dam_search_query",
        "سد"
    )

    if not result_indexes:

        await query.edit_message_text(

            "🔎 نتیجه‌ای پیدا نشد.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏗 همه سدها",
                        callback_data="dams:0"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="back_start"
                    )
                ]

            ])

        )

        return

    message, keyboard = build_search_page(
        result_indexes,
        page,
        search_query
    )

    await query.edit_message_text(

        message,

        reply_markup=keyboard,

        parse_mode="HTML"
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
    # جغرافیا
    # -----------------------------------------------------

    if data == "geo_provinces":

        await show_provinces(query)

        return

    # -----------------------------------------------------
    # ولایت
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
    # ولسوالی
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
    # فهرست سدها + صفحه‌بندی
    # -----------------------------------------------------

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
    # اطلاعات یک سد
    # -----------------------------------------------------

    if data.startswith("dam:"):

        dam_index = data.split(
            ":",
            1
        )[1]

        await show_single_dam(
            query,
            dam_index
        )

        return

    # -----------------------------------------------------
    # صفحه جستجو
    # -----------------------------------------------------

    if data.startswith("dsearch:"):

        try:

            page = int(
                data.split(
                    ":",
                    1
                )[1]
            )

        except ValueError:

            page = 0

        await show_dam_search_page(
            query,
            context,
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
    # منوی اصلی
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
# جستجوی متنی
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_query = update.message.text.strip()

    if not user_query:

        return

    query_lower = user_query.lower()

    # -----------------------------------------------------
    # کلمات مرتبط با سد
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # جستجوی سد
    # -----------------------------------------------------

    if is_dam_search:

        # اگر فقط «سد» یا «بند» نوشته شد
        if query_lower in (
            "بند",
            "سد",
            "dam",
            "dams"
        ):

            result_indexes = list(
                range(len(DAMS))
            )

        else:

            result_indexes = search_dams(
                user_query
            )

        if not result_indexes:

            await update.message.reply_text(

                "🔎 بندی با این جستجو پیدا نشد."

            )

            return

        # ذخیره برای صفحه‌های بعد
        context.user_data[
            "dam_search_indexes"
        ] = result_indexes

        context.user_data[
            "dam_search_query"
        ] = user_query

        message, keyboard = build_search_page(

            result_indexes,

            0,

            user_query

        )

        await update.message.reply_text(

            message,

            reply_markup=keyboard,

            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # جستجوی عمومی پایگاه داده
    # -----------------------------------------------------

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
        f"«{escape(user_query)}»</b>\n\n"
    )

    for i, result in enumerate(
        results,
        1
    ):

        _, title, category, content = result

        message += (
            f"📌 {i}. {escape(str(title))}\n"
            f"📂 {escape(str(category))}\n"
            f"📝 {escape(str(content)[:500])}\n\n"
        )

    await update.message.reply_text(

        message[:4000],

        parse_mode="HTML"
    )


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
    print(
        f"📄 تعداد سد در هر صفحه: "
        f"{DAMS_PER_PAGE}"
    )
    print(
        f"📑 تعداد صفحات سدها: "
        f"{total_pages(DAMS)}"
    )
    print("=" * 60)

    # -----------------------------------------------------
    # Render Web Server
    # -----------------------------------------------------

    keep_alive()

    print(
        "🌐 Render Keep-Alive فعال شد."
    )

    # -----------------------------------------------------
    # Telegram Bot
    # -----------------------------------------------------

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # Commands
    # -----------------------------------------------------

    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )

    # -----------------------------------------------------
    # Callback buttons
    # -----------------------------------------------------

    app.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )

    # -----------------------------------------------------
    # Text search
    # -----------------------------------------------------

    app.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
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
