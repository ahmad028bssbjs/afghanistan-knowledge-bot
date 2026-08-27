import os
import json
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
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
# سرور HTTP برای Render
# =========================================================

class HealthHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"Afghanistan Knowledge Bot is running."
        )

    def log_message(self, format, *args):
        pass


def run_health_server():

    port = int(
        os.environ.get("PORT", "8080")
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print("=" * 60)
    print(f"🌐 Render HTTP server running on port {port}")
    print("=" * 60)

    server.serve_forever()


threading.Thread(
    target=run_health_server,
    daemon=True
).start()


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# اطلاعات سدها
# =========================================================

DAM_FILE = (
    "data/dams/"
    "geodar_afghanistan_complete.json"
)


def load_dams():

    if not os.path.exists(DAM_FILE):

        print("=" * 60)
        print("⚠️ فایل اطلاعات سدها پیدا نشد:")
        print(DAM_FILE)
        print("=" * 60)

        return []

    try:

        with open(
            DAM_FILE,
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        # فایل کامل شما ساختار:
        # {
        #   country: ...,
        #   count: ...,
        #   dams: [...]
        # }

        if isinstance(data, dict):

            dams = data.get("dams", [])

        elif isinstance(data, list):

            dams = data

        else:

            dams = []

        print("=" * 60)
        print("✅ اطلاعات سدها بارگذاری شد")
        print(f"فایل: {DAM_FILE}")
        print(f"تعداد سدها: {len(dams)}")
        print("=" * 60)

        return dams

    except Exception as e:

        print("=" * 60)
        print("❌ خطا در خواندن اطلاعات سدها")
        print(e)
        print("=" * 60)

        return []


DAMS = load_dams()


# =========================================================
# نام سد
# =========================================================

DAM_NAMES = {

    "1": "Band-e Sarda",

    "2": "Kajaki Dam",

    "3": "Sarobi Dam",

    "4": "Darunta Dam",

    "5": "Dahla Dam",

    "23506": "Naghlu Dam",

    "24517": "Salma Dam"

}


def get_dam_id(dam):

    return str(
        dam.get(
            "geodar_id",
            dam.get(
                "id_v11",
                dam.get(
                    "OBJECTID",
                    ""
                )
            )
        )
    )


def get_dam_name(dam):

    dam_id = get_dam_id(dam)

    return DAM_NAMES.get(
        dam_id,
        dam.get(
            "name",
            f"Dam #{dam_id}"
        )
    )


# =========================================================
# جستجوی سد
# =========================================================

def search_dams(query):

    query = query.lower().strip()

    results = []

    for dam in DAMS:

        name = get_dam_name(dam)

        text = " ".join(
            str(value)
            for value in dam.values()
        )

        text += " " + name

        if query in text.lower():

            results.append(dam)

    return results


# =========================================================
# نمایش اطلاعات سد
# =========================================================

def dam_text(dam, number=None):

    dam_id = get_dam_id(dam)

    name = get_dam_name(dam)

    province = dam.get(
        "province",
        "ثبت نشده"
    )

    district = dam.get(
        "district",
        "ثبت نشده"
    )

    center = dam.get(
        "province_center",
        "ثبت نشده"
    )

    distance = dam.get(
        "distance_to_province_center_km",
        "ثبت نشده"
    )

    lat = dam.get(
        "latitude",
        dam.get("lat", "")
    )

    lon = dam.get(
        "longitude",
        dam.get("lon", "")
    )

    grand_id = dam.get(
        "grand_id",
        dam.get(
            "id_grd_v13",
            "-999"
        )
    )

    geo_method = dam.get(
        "geo_method",
        dam.get(
            "geo_mtd",
            ""
        )
    )

    qa_rank = dam.get(
        "qa_rank",
        ""
    )

    volume = dam.get(
        "reservoir_volume_mcm_v11",
        dam.get(
            "rv_mcm_v11",
            ""
        )
    )

    source = dam.get(
        "source",
        dam.get(
            "harmonization_source",
            ""
        )
    )

    if grand_id in ("", "-999", "-999.0", None):
        grand_id = "ثبت نشده"

    if volume in ("", "-999", "-999.0", None):
        volume = "ثبت نشده"

    if not geo_method:
        geo_method = "ثبت نشده"

    if not qa_rank:
        qa_rank = "ثبت نشده"

    if not source:
        source = "ثبت نشده"

    title = ""

    if number is not None:

        title = (
            f"🔢 سد شماره {number}\n\n"
        )

    text = (
        title

        + f"🏗 **{name}**\n\n"

        + f"🆔 GeoDAR ID: `{dam_id}`\n\n"

        + f"🇦🇫 ولایت: {province}\n"

        + f"🏘 ولسوالی: {district}\n"

        + f"🏙 مرکز ولایت: {center}\n"

        + f"📏 فاصله تا مرکز: "
        f"{distance} km\n\n"

        + "📍 **مختصات:**\n"

        + f"عرض: {lat}\n"

        + f"طول: {lon}\n\n"

        + f"🆔 GRanD ID: {grand_id}\n\n"

        + "🛰 **روش تعیین موقعیت:**\n"

        + f"{geo_method}\n\n"

        + f"✅ **رتبه کیفیت:** {qa_rank}\n\n"

        + "💧 **حجم مخزن:**\n"

        + f"{volume} MCM\n\n"

        + f"📚 **منبع:** {source}"
    )

    return text


# =========================================================
# دکمه‌های نقشه برای هر سد
# =========================================================

def dam_map_button(dam):

    name = get_dam_name(dam)

    lat = dam.get(
        "latitude",
        dam.get("lat")
    )

    lon = dam.get(
        "longitude",
        dam.get("lon")
    )

    if lat is None or lon is None:
        return None

    url = (
        "https://www.google.com/maps/search/"
        f"?api=1&query={lat},{lon}"
    )

    return InlineKeyboardButton(
        f"📍 {name} روی نقشه",
        url=url
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

        "یک موضوع را جستجو کن "
        "یا از منوی زیر استفاده کن.\n\n"

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
# نمایش ۳۴ ولایت
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
# اطلاعات ولسوالی
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

        f"🏛 ولایت: "
        f"{district['province_fa']}\n\n"

        f"🇬🇧 نام انگلیسی: "
        f"{district['district_name_en']}\n\n"

        f"🆔 شناسه ولسوالی: "
        f"{district['district_id']}\n\n"

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
# نمایش سدها
# =========================================================

async def show_dams(query):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.\n\n"

            f"فایل مورد انتظار:\n"
            f"{DAM_FILE}",

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

    message = (
        "🏗 **بندها و سدهای افغانستان**\n\n"

        f"تعداد سدهای ثبت‌شده: "
        f"{len(DAMS)}\n\n"

        "━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    for index, dam in enumerate(
        DAMS[:20],
        1
    ):

        message += (
            dam_text(
                dam,
                index
            )

            + "\n\n"

            + "━━━━━━━━━━━━━━\n\n"
        )

        map_button = dam_map_button(dam)

        if map_button:

            buttons.append([map_button])

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    # تلگرام حدود 4096 کاراکتر قبول می‌کند
    # برای اطمینان کمی پایین‌تر نگه می‌داریم.

    if len(message) > 3900:

        message = message[:3850]

        message += (
            "\n\n⚠️ ادامه اطلاعات "
            "در نسخه بعدی صفحه‌بندی می‌شود."
        )

    await query.edit_message_text(

        message,

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# دکمه‌ها
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
    # باز
