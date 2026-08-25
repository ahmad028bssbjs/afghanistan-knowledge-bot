import json
from database import add_document


INPUT_FILE = "reservoirs.json"


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)


    count = 0

    for item in data:

        add_document(
            item["title"],
            item["category"],
            item["content"]
        )

        count += 1


    print(
        f"🇦🇫 {count} رکورد مخزن وارد دیتابیس شد."
    )


if __name__ == "__main__":
    main()
