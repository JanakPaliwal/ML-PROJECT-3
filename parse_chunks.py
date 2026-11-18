import re
import json

def parse_html(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"\n--- Parsing {filename} ---")
    
    # Check for next.js f.push chunks
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', content)
    print(f"Total Next.js streaming chunks: {len(chunks)}")
    
    # Concatenate chunks and unescape
    full_stream = "".join(chunks).replace('\\"', '"').replace('\\\\', '\\')
    
    # Search for prices, dates, history
    # Let's search for "history" or "priceHistory" or "chartData" or dates like "2026-10" or "2026-11" or "2024" or "2023"
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', full_stream)
    print(f"Found {len(dates)} dates. Unique dates: {sorted(list(set(dates)))[:10]} ... {sorted(list(set(dates)))[-10:]}")
    
    # Search for occurrences of price keys
    sub_matches = re.findall(r'(\{[^{}]*?"date"[^{}]*?"price"[^{}]*?\})', full_stream)
    if sub_matches:
        print(f"Found date/price objects: {len(sub_matches)}")
        print("Sample:", sub_matches[:5])
    else:
        # Let's find where 'Median mandi price' or 'price-history' appears
        idx = full_stream.find("price-history")
        if idx != -1:
            print("Around price-history:", full_stream[max(0, idx-200):min(len(full_stream), idx+600)])
        idx2 = full_stream.find("quintal")
        if idx2 != -1:
            print("Around quintal:", full_stream[max(0, idx2-200):min(len(full_stream), idx2+600)])

parse_html("tomato_page.html")
parse_html("onion_page.html")
