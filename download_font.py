import requests
import os

url = "https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Regular.ttf"
url_bold = "https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Bold.ttf"

for filename, link in [("Sarabun-Regular.ttf", url), ("Sarabun-Bold.ttf", url_bold)]:
    r = requests.get(link)
    with open(filename, "wb") as f:
        f.write(r.content)
    print(f"ดาวน์โหลด {filename} เสร็จแล้ว")