import re
import json
import pandas as pd

def extract_points(filename, crop):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', content)
    full_stream = "".join(chunks).replace('\\"', '"').replace('\\\\', '\\')
    
    # Locate points in section id price-history
    idx = full_stream.find('"id":"price-history"')
    if idx == -1:
        print("Not found price-history")
        return []
    
    sub = full_stream[idx:idx+25000]
    points_idx = sub.find('"points":[')
    if points_idx == -1:
        print("Not found points")
        return []
    
    # Extract the JSON array of points
    start = idx + points_idx + len('"points":')
    # scan until matching bracket
    depth = 0
    end = start
    for i in range(start, len(full_stream)):
        if full_stream[i] == '[':
            depth += 1
        elif full_stream[i] == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    points_json_str = full_stream[start:end]
    points = json.loads(points_json_str)
    print(f"Extracted {len(points)} points for {crop}:")
    
    records = []
    for pt in points:
        fig = pt.get("figure", {})
        dt = pt.get("date")
        price = fig.get("price")
        mandis = fig.get("mandis")
        arrivals = pt.get("arrivals", {}).get("totalTonnes") if isinstance(pt.get("arrivals"), dict) else None
        low = fig.get("low", {}).get("price")
        high = fig.get("high", {}).get("price")
        records.append({
            "crop": crop,
            "date": dt,
            "median_price": price,
            "low_price": low,
            "high_price": high,
            "mandis_reporting": mandis,
            "arrivals_tonnes": arrivals
        })
    df = pd.DataFrame(records)
    print(df.head(10))
    print(df.tail(10))
    return df

df_tomato = extract_points("tomato_page.html", "tomato")
df_onion = extract_points("onion_page.html", "onion")

df_tomato.to_csv("tomato_real_dataset.csv", index=False)
df_onion.to_csv("onion_real_dataset.csv", index=False)
print("Saved tomato_real_dataset.csv and onion_real_dataset.csv successfully!")
