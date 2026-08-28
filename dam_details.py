# =========================================================
# dam_details.py
# اطلاعات و مشخصات سدهای افغانستان
# =========================================================


# =========================================================
# تبدیل مقدار خالی
# =========================================================

def clean_value(value, default="ثبت نشده"):
    """
    مقدارهای خالی یا نامعتبر را به مقدار قابل نمایش تبدیل می‌کند.
    """

    if value is None:
        return default

    # اگر لیست یا دیکشنری بود
    if isinstance(value, (list, dict)):
        if not value:
            return default
        return str(value)

    value = str(value).strip()

    if value in (
        "",
        "-999",
        "-999.0",
        "-999.00",
        "None",
        "none",
        "null",
        "NULL",
        "NaN",
        "nan",
    ):
        return default

    return value


# =========================================================
# نام فارسی سد
# =========================================================

def get_dam_name_fa(dam):
    """
    نام فارسی سد را از JSON استخراج می‌کند.
    """

    if not isinstance(dam, dict):
        return "سد بدون نام"

    name = (
        dam.get("name_fa")
        or dam.get("dam_name_fa")
        or dam.get("name")
        or dam.get("dam_name")
    )

    return clean_value(
        name,
        "سد بدون نام"
    )


# =========================================================
# نام انگلیسی سد
# =========================================================

def get_dam_name_en(dam):
    """
    نام انگلیسی سد را از JSON استخراج می‌کند.
    """

    if not isinstance(dam, dict):
        return ""

    name = (
        dam.get("name_en")
        or dam.get("dam_name_en")
        or dam.get("english_name")
    )

    value = clean_value(
        name,
        ""
    )

    if value == "ثبت نشده":
        return ""

    return value


# =========================================================
# استخراج مختصات
# =========================================================

def get_coordinates(dam):
    """
    مختصات سد را با پشتیبانی از چند نام احتمالی فیلدها
    از اطلاعات JSON استخراج می‌کند.

    خروجی:
        (latitude, longitude)
    """

    if not isinstance(dam, dict):
        return None, None

    latitude = (
        dam.get("latitude")
        or dam.get("lat")
        or dam.get("Latitude")
        or dam.get("LAT")
    )

    longitude = (
        dam.get("longitude")
        or dam.get("lon")
        or dam.get("lng")
        or dam.get("Longitude")
        or dam.get("LON")
        or dam.get("LONG")
    )

    # -----------------------------------------------------
    # اگر مختصات داخل یک فیلد coordinates باشد
    # -----------------------------------------------------

    if (
        (latitude is None or longitude is None)
        and dam.get("coordinates") is not None
    ):

        coordinates = dam.get(
            "coordinates"
        )

        if isinstance(
            coordinates,
            (list, tuple)
        ):

            # معمولاً GeoJSON به شکل [longitude, latitude]
            if len(coordinates) >= 2:

                longitude = coordinates[0]
                latitude = coordinates[1]

        elif isinstance(
            coordinates,
            dict
        ):

            latitude = (
                coordinates.get("latitude")
                or coordinates.get("lat")
                or latitude
            )

            longitude = (
                coordinates.get("longitude")
                or coordinates.get("lon")
                or coordinates.get("lng")
                or longitude
            )

    # -----------------------------------------------------
    # تبدیل به float
    # -----------------------------------------------------

    try:

        if latitude is not None:
            latitude = float(latitude)

    except (
        ValueError,
        TypeError
    ):

        latitude = None

    try:

        if longitude is not None:
            longitude = float(longitude)

    except (
        ValueError,
        TypeError
    ):

        longitude = None

    # -----------------------------------------------------
    # بررسی محدوده مختصات
    # -----------------------------------------------------

    if latitude is not None:

        if latitude < -90 or latitude > 90:
            latitude = None

    if longitude is not None:

        if longitude < -180 or longitude > 180:
            longitude = None

    return latitude, longitude


# =========================================================
# وضعیت سد
# =========================================================

def get_status_fa(status):
    """
    تبدیل وضعیت انگلیسی به فارسی.
    """

    status = clean_value(
        status
    )

    statuses = {

        "active":
            "فعال",

        "under_construction":
            "در حال ساخت",

        "proposed":
            "پیشنهادی",

        "active_partially":
            "فعال به‌صورت جزئی",

        "inactive":
            "غیرفعال",

        "planned":
            "برنامه‌ریزی‌شده",

        "completed":
            "تکمیل‌شده",

        "unknown":
            "نامشخص"
    }

    return statuses.get(
        status,
        status
    )


# =========================================================
# ساخت متن کامل اطلاعات سد
# =========================================================

def build_dam_text(
    dam,
    number=None
):
    """
    اطلاعات کامل یک سد را برای نمایش در تلگرام می‌سازد.
    """

    if not isinstance(dam, dict):

        return (
            "❌ اطلاعات سد نامعتبر است."
        )

    # -----------------------------------------------------
    # اطلاعات پایه
    # -----------------------------------------------------

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

    status = get_status_fa(
        dam.get("status")
    )

    # -----------------------------------------------------
    # شناسه‌ها
    # -----------------------------------------------------

    geodar_id = clean_value(
        dam.get("geodar_id")
        or dam.get("id_v11")
        or dam.get("geodar")
    )

    grand_id = clean_value(
        dam.get("grand_id")
        or dam.get("id_grd_v13")
        or dam.get("grand")
    )

    # -----------------------------------------------------
    # مختصات
    # -----------------------------------------------------

    latitude, longitude = get_coordinates(
        dam
    )

    lat = clean_value(
        latitude
    )

    lon = clean_value(
        longitude
    )

    # -----------------------------------------------------
    # مرکز ولایت
    # -----------------------------------------------------

    province_center = clean_value(
        dam.get("province_center")
        or dam.get("province_center_name")
    )

    distance = clean_value(
        dam.get(
            "distance_to_province_center_km"
        )
    )

    # -----------------------------------------------------
    # اطلاعات جغرافیایی / کیفیت
    # -----------------------------------------------------

    geo_method = clean_value(
        dam.get("geo_method")
        or dam.get("geo_mtd")
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    source = clean_value(
        dam.get("source")
        or dam.get("val_src")
        or dam.get("har_src")
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    height = clean_value(
        dam.get("height_m")
        or dam.get("height")
    )

    storage = clean_value(
        dam.get(
            "storage_capacity_mcm"
        )
        or dam.get(
            "reservoir_volume_mcm_v11"
        )
        or dam.get(
            "rv_mcm_v11"
        )
        or dam.get(
            "storage_mcm"
        )
    )

    power = clean_value(
        dam.get("power_capacity_mw")
        or dam.get("power_mw")
        or dam.get("capacity_mw")
    )

    irrigation = clean_value(
        dam.get("irrigation_area_ha")
        or dam.get("irrigation_ha")
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

    # -----------------------------------------------------
    # شماره
    # -----------------------------------------------------

    if number is not None:

        text += (
            f"🔢 <b>سد شماره {number}</b>\n\n"
        )

    # -----------------------------------------------------
    # نام
    # -----------------------------------------------------

    text += (
        f"🏗 <b>{name_fa}</b>\n"
    )

    if name_en:

        text += (
            f"🇬🇧 {name_en}\n"
        )

    text += "\n"

    # -----------------------------------------------------
    # موقعیت
    # -----------------------------------------------------

    text += (
        "📍 <b>موقعیت</b>\n"
        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {province_center}\n"
        f"📏 فاصله تا مرکز ولایت: "
        f"{distance} km\n"
        f"📌 وضعیت: {status}\n\n"
    )

    # -----------------------------------------------------
    # مختصات
    # -----------------------------------------------------

    text += (
        "🌐 <b>مختصات جغرافیایی</b>\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    text += (
        "🏗 <b>اطلاعات فنی</b>\n"
        f"📏 ارتفاع دیواره: "
        f"{height} متر\n"
        f"💧 ظرفیت ذخیره: "
        f"{storage} میلیون متر مکعب\n"
        f"⚡ ظرفیت برق: "
        f"{power} مگاوات\n"
        f"🌾 مساحت آبیاری: "
        f"{irrigation} هکتار\n\n"
    )

    # -----------------------------------------------------
    # شناسه پایگاه داده
    # -----------------------------------------------------

    text += (
        "🆔 <b>اطلاعات پایگاه داده</b>\n"
        f"GeoDAR ID: {geodar_id}\n"
        f"GRanD ID: {grand_id}\n\n"
    )

    # -----------------------------------------------------
    # روش تعیین موقعیت
    # -----------------------------------------------------

    text += (
        "🛰 <b>روش تعیین موقعیت</b>\n"
        f"{geo_method}\n\n"
    )

    # -----------------------------------------------------
    # کنترل کیفیت
    # -----------------------------------------------------

    text += (
        "✅ <b>رتبه کنترل کیفیت</b>\n"
        f"{qa_rank}\n\n"
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    if description:

        text += (
            "📖 <b>توضیحات</b>\n"
            f"{description}\n\n"
        )

    # -----------------------------------------------------
    # موقعیت و محل
    # -----------------------------------------------------

    if location_description:

        text += (
            "📍 <b>موقعیت و محل سد</b>\n"
            f"{location_description}\n\n"
        )

    # -----------------------------------------------------
    # نوع سد
    # -----------------------------------------------------

    if type_description:

        text += (
            "🏗 <b>نوع سد</b>\n"
            f"{type_description}\n\n"
        )

    # -----------------------------------------------------
    # تاریخچه
    # -----------------------------------------------------

    if history_description:

        text += (
            "📜 <b>تاریخچه و ساخت</b>\n"
            f"{history_description}\n\n"
        )

    # -----------------------------------------------------
    # کاربرد
    # -----------------------------------------------------

    if purpose_description:

        text += (
            "🎯 <b>کاربرد</b>\n"
            f"{purpose_description}\n\n"
        )

    # -----------------------------------------------------
    # اهمیت
    # -----------------------------------------------------

    if importance_description:

        text += (
            "⭐ <b>اهمیت</b>\n"
            f"{importance_description}\n\n"
        )

    # -----------------------------------------------------
    # برق
    # -----------------------------------------------------

    if power_description:

        text += (
            "⚡ <b>برق و ظرفیت تولید</b>\n"
            f"{power_description}\n\n"
        )

    # -----------------------------------------------------
    # منبع
    # -----------------------------------------------------

    text += (
        "📚 <b>منبع</b>\n"
        f"{source}"
    )

    return text
