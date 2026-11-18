import re
import json

def find_history_chart_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', content)
    full_stream = "".join(chunks).replace('\\"', '"').replace('\\\\', '\\')
    
    # Look for chart / history patterns
    # In the screenshot: "30 calendar days: 20 Oct 2026 - 18 Nov 2026 (IST). Only reported dates are plotted."
    # "Median mandi price (₹/quintal)"
    print(f"\n=== Searching history data in {filename} ===")
    
    # Let's search for "30 calendar days" or "Median mandi price"
    for term in ["30 calendar days", "Median mandi price", "price-history", "history"]:
        pos = 0
        while True:
            idx = full_stream.find(term, pos)
            if idx == -1:
                break
            print(f"Found '{term}' at {idx}:")
            snippet = full_stream[max(0, idx-100):min(len(full_stream), idx+500)]
            print(snippet)
            print("-" * 50)
            pos = idx + len(term) + 50

find_history_chart_data("tomato_page.html")
find_history_chart_data("onion_page.html")
