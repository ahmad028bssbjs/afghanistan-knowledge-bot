from database import add_document


test_documents = [
    {
        "title": "کابل",
        "category": "جغرافیا",
        "content": "کابل پایتخت افغانستان است و در بخش شرقی کشور قرار دارد."
    },
    {
        "title": "غزنی",
        "category": "جغرافیا",
        "content": "غزنی یکی از شهرهای تاریخی افغانستان است و در دوره غزنویان اهمیت زیادی داشت."
    },
    {
        "title": "هرات",
        "category": "جغرافیا",
        "content": "هرات یکی از شهرهای مهم تاریخی و فرهنگی افغانستان در غرب کشور است."
    },
    {
        "title": "بند کجکی",
        "category": "بندها",
        "content": "بند کجکی یک بند بزرگ در ولایت هلمند افغانستان است."
    },
    {
        "title": "احمدشاه ابدالی",
        "category": "تاریخ",
        "content": "احمدشاه ابدالی بنیان‌گذار امپراتوری درانی بود و در تاریخ افغانستان جایگاه مهمی دارد."
    }
]


def main():
    for item in test_documents:
        add_document(
            item["title"],
            item["category"],
            item["content"]
        )

    print("🇦🇫 داده‌های آزمایشی وارد دیتابیس شدند.")


if __name__ == "__main__":
    main()
