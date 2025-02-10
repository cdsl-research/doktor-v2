import json
import os
import re
import sys
from datetime import datetime as dt

import requests

DEBUG = False


def parse_datetime(raw_datetime: str) -> dt:
    raw_datetime = raw_datetime.replace(".", " ").strip()
    _month, _day, _year = raw_datetime.split()
    _month = _month[:3]  # June -> Jun
    _day = _day.zfill(2)  # 3 -> 03
    datetime_obj = dt.strptime(f"{_month} {_day} {_year} +0900", "%b %d %Y %z")
    return datetime_obj


def main():
    PAPER_URL = os.getenv(
        "PAPER_PUBLISH_URL",
        "https://ja.tak-cslab.org/tech-report")
    try:
        response = requests.get(PAPER_URL)
    except Exception:
        print("Failed to get content")
        sys.exit(1)

    # print(response.text)
    lines = response.text.split("\n")
    _month = None
    matched_papers = []
    for line in lines:
        # skipping empty line
        if not line:
            continue

        # find: 2020年7月
        line_dt = re.search(r"\d+年\d+月", line)
        if line_dt is not None and len(line_dt.string) < 50:  # match
            _month = line_dt.group(0)
            # print(line_dt.string)

        # skipping unset month
        if _month is None:
            continue

        # retrieve paper info
        papers = re.findall(r"<li>.*?</li>", line)
        if len(papers) < 1:  # unmatched
            continue

        for paper in papers:
            # find: <a>xxx</a>
            paper_detail_raw = re.search(r"<a [^>]+>(.*?)</a>", paper)
            if paper_detail_raw is None:
                continue

            # find: href="xxx"
            paper_url = re.search(
                r'href="https://drive.google.com/file/d/([-\w]+)',
                paper_detail_raw.string,
            )
            if paper_url is None:
                continue
            paper_url_id = paper_url.groups()[0]

            # internal <a> tag
            paper_detail = paper_detail_raw.groups()[0]
            # Fix typo
            paper_detail = paper_detail.replace("CDSL -TR", "CDSL-TR").replace(
                "&#8221;", '"'
            )
            if DEBUG:
                print("Raw:", paper_detail)

            # split title, author, paper_id, datetime
            parts = re.split(r"\. |, |,|，|\&#\d+;|\"|”", paper_detail)
            itr_parts = iter(parts)

            try:
                """find: author"""
                paper_authors = []
                while True:
                    author = next(itr_parts)
                    if DEBUG:
                        print("'" + author + "'")
                    if author.strip() == "":
                        break
                    paper_authors.append(author.strip())
                if DEBUG:
                    print(f"{paper_authors=}")

                """ find: title """
                title = ""
                while True:
                    t = next(itr_parts)
                    # print(t)
                    if len(t.strip()) > 3:
                        title = t.strip()
                        if title.endswith(","):
                            title = title[:-1]
                        break
                if DEBUG:
                    print(f"{title=}")

                """ find: paper_id """
                paper_id = ""
                while True:
                    t = next(itr_parts)
                    # print(t)
                    if t.strip().startswith("CDSL-TR"):
                        paper_id = t.strip()
                        break
                if DEBUG:
                    print(f"{paper_id=}")

                """ find: datetime """
                _dt = " ".join(itr_parts)
                matched_dt_str = re.findall(
                    r"\w{3,5}\.?\s*\d{1,2}[.,]?\s*\d{4}", _dt)
                if len(matched_dt_str) > 2:
                    print("+" * 10, "Unexpected datetime:", matched_dt_str)
                if DEBUG:
                    print(f"{matched_dt_str=}")

                if len(matched_dt_str) == 0:
                    print("+" * 10, "ERROR: fail to parse", paper_detail)
                    continue

                """ fix typo """
                matched_dt_str[0] = matched_dt_str[0].replace("Arp", "Apr")

                """ parse datetime string """
                dt_created_at = parse_datetime(matched_dt_str[0])
                created_at = dt_created_at.isoformat()
                if DEBUG:
                    print(f"{created_at=}")

                updated_at = ""
                if len(matched_dt_str) == 2:
                    dt_updated_at = parse_datetime(matched_dt_str[1])
                    updated_at = dt_updated_at.isoformat()

                matched_papers.append(
                    {
                        "author": paper_authors,
                        "title": title,
                        "paper_id": paper_id,
                        "datetime": _dt,
                        "paper_url_id": paper_url_id,
                        "created_at": created_at,
                        "updated_at": updated_at,
                    }
                )

            except StopIteration:
                print("+" * 10, "ERROR: exception", paper_detail)
                continue

    # print(json.dumps(matched_papers, indent=4))
    with open("papers.json", mode="w") as f:
        json.dump(matched_papers, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
