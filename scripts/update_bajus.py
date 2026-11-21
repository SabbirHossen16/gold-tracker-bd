#!/usr/bin/env python3
"""Check the current BAJUS gold rates and update data/bajus.json when they change.

Reads the BAJUS rates as republished on goldratebangladesh.today (the official
bajus.org site blocks automated visitors). Uses only the Python standard library.
The file is written only when BAJUS has changed its rates, plus a small
heartbeat every 25 days so GitHub keeps the hourly schedule running.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

URL = "https://goldratebangladesh.today/"
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "bajus.json")
BHORI_G = 11.664
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; gold-tracker-bd/1.0; +https://github.com/SabbirHossen16/gold-tracker-bd)",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def to_int(s):
    return int(s.replace(",", ""))


def parse(page):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", text))
    text = re.sub(r"[ \t ]+", " ", text)

    def grade(label):
        m = re.search(label + r"\s*৳\s*([\d,]+)\s*/\s*vori\s*৳\s*([\d,]+)\s*/\s*gram", text, flags=re.I)
        if not m:
            raise ValueError("could not find the %s rate" % label)
        return to_int(m.group(1)), to_int(m.group(2))

    rates = {}
    for key, label in (("k22", "22K Gold"), ("k21", "21K Gold"), ("k18", "18K Gold"), ("trad", "Traditional Gold")):
        per_bhori, per_gram = grade(label)
        if abs(per_gram * BHORI_G - per_bhori) > per_bhori * 0.01:
            raise ValueError("%s per gram and per vori do not agree" % label)
        rates[key] = per_bhori

    m = re.search(r"Rate effective:\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m or m.group(2).lower() not in MONTHS:
        raise ValueError("could not find the effective date")
    date = dt.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
    return date, rates


def sane(date, rates, previous):
    if not (50_000 < rates["k22"] < 1_000_000):
        return "22K rate out of range"
    if not (rates["k22"] > rates["k21"] > rates["k18"] > rates["trad"] > 0):
        return "grades are not in the usual order"
    if previous and abs(rates["k22"] / previous["k22"] - 1) > 0.20:
        return "22K moved more than 20% in one step"
    if previous and date < previous["date"]:
        return "effective date is older than the saved one"
    today = dt.datetime.now(dt.timezone.utc).date()
    if dt.date.fromisoformat(date) > today + dt.timedelta(days=2):
        return "effective date is in the future"
    return None


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    previous = data.get("latest")

    date, rates = parse(fetch(URL))
    problem = sane(date, rates, previous)
    if problem:
        print("Not updating: " + problem, date, rates)
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    changed = (not previous) or previous.get("date") != date or any(previous.get(k) != v for k, v in rates.items())
    last_check = dt.datetime.fromisoformat(data.get("checked_at", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00"))
    heartbeat = now - last_check > dt.timedelta(days=25)

    if changed:
        data["latest"] = dict(date=date, **rates)
        hist = [h for h in data.get("history", []) if h[0] != date]
        hist.append([date, rates["k22"]])
        data["history"] = sorted(hist)
        print("BAJUS rate changed:", date, rates)
    else:
        print("No change:", date, rates)

    if changed or heartbeat:
        data["checked_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write("\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # a failed check must never damage the saved data
        print("Check failed:", e)
        sys.exit(1)
