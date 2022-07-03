import json

"""
{
  "first_name_ja": "太郎",
  "last_name_ja": "工科",
  "first_name_en": "Taro",
  "last_name_en": "Kouka",
  "joined_year": 2019,
  "graduation": true
},
"""


def main():
    with open("papers.json") as f:
        papers = json.load(f)
    # for p in papers:
    #     print(p)

    """ Create unique author list from papers.json """
    authors = set()
    for p in papers:
        authors = authors | set(p["author"])
    # print(authors)

    write_buffer = []
    for author in authors:
        try:
            last_name_ja, first_name_ja = author.split(" ")
        except Exception:
            print("Exception:", author)
        write_buffer.append(
            {
                "first_name_ja": first_name_ja,
                "last_name_ja": last_name_ja,
            }
        )

    import datetime

    current = datetime.datetime.now()
    dt = current.strftime("%Y%m%d")
    with open(f"_authors.{dt}.json", mode="w") as f:
        json.dump(write_buffer, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
