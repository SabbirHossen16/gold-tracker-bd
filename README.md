# সোনার দাম ট্র্যাকার: বাংলাদেশ (Gold price tracker: Bangladesh)

**Live page:** https://sabbirhossen16.github.io/gold-tracker-bd/

- বাজুস (BAJUS) নির্ধারিত সোনার দাম, প্রতি ঘণ্টায় স্বয়ংক্রিয়ভাবে যাচাই করা হয়।
- বিশ্ববাজারে সোনার দাম, পেজ খোলা থাকলে প্রতি মিনিটে হালনাগাদ হয়।
- বাজুস পরবর্তী দফায় দাম কমাবে কি না, তার একটি সম্ভাব্য হিসাব।

## How it updates

- `.github/workflows/update-bajus.yml` runs every hour. It runs `scripts/update_bajus.py`, which reads the BAJUS rates
  as republished on goldratebangladesh.today and saves them to `data/bajus.json` only when they change.
- The page (`index.html`) reads `data/bajus.json`, and fetches the world gold price (gold-api.com, backup xaus.com),
  daily history (xaus.com) and the US dollar to taka rate (open.er-api.com) directly in the visitor's browser.

For information only, not financial advice.
