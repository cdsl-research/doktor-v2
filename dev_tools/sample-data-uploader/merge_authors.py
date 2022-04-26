import datetime
import glob
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
    """ Open cached author list """
    with open("authors.json") as f:
        total_authors = json.load(f)
    uniq_names = {a["last_name_ja"]+" "+a["first_name_ja"]
                  for a in total_authors}
    # print(uniq_names)

    """ Open new author list """
    write_buffer = {}
    author_files = glob.glob("_authors.*.json")
    for fname in author_files:
        with open(fname) as f:
            body = json.load(f)
        for author in body:
            au = author["last_name_ja"]+" "+author["first_name_ja"]
            if au in uniq_names:  # found author
                pass
            else:  # not found author
                # print(au)
                cur = datetime.datetime.now()
                write_buffer[au] = {
                    "first_name_ja": author["first_name_ja"],
                    "last_name_ja": author["last_name_ja"],
                    "first_name_en": "",
                    "last_name_en": "",
                    "joined_year": cur.strftime("%Y"),
                    "graduation": False,
                }

    """ Add new author to cached author list """
    new_authors = list(write_buffer.values())
    total_authors += new_authors
    # print(json.dumps(total_authors, indent=4, ensure_ascii=False))
    with open("authors.json", mode='w') as f:
        json.dump(total_authors, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
