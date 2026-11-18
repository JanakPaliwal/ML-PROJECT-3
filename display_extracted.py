import pandas as pd

df_tomato = pd.read_csv("tomato_real_dataset.csv")
df_onion = pd.read_csv("onion_real_dataset.csv")

print("=== Tomato 30-Day Extracted History (Matches Picture 1) ===")
print(df_tomato[['date', 'median_price', 'low_price', 'high_price', 'mandis_reporting']].to_string())

print("\n=== Onion 30-Day Extracted History (Matches Picture 2) ===")
print(df_onion[['date', 'median_price', 'low_price', 'high_price', 'mandis_reporting']].to_string())
