import urllib.request
import re
import json

def fetch_and_extract(crop_name):
    url = f"https://acrop.app/prices/{crop_name}"
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    
    with open(f"{crop_name}_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {crop_name}_page.html ({len(html)} bytes)")

    # Find numbers and dates or JSON structures
    # Let's search for occurrences of 'price' or 'median' or numbers like 2625, 3255, 4835, 5775
    # or Next.js state
    patterns = [r'\{"date":.*?\bprice\b.*?\}', r'\{[^{}]*3255[^{}]*\}', r'\{[^{}]*5775[^{}]*\}', r'\[[0-9,\.\s]{10,}\]']
    for p in patterns:
        m = re.findall(p, html)
        if m:
            print(f"Match pattern {p}: found {len(m)} items. Sample: {m[:2]}")

fetch_and_extract("tomato")
fetch_and_extract("onion")
