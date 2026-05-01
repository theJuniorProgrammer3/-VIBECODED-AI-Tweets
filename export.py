# export_data.py
import json
from a_fast2 import TextQuilter

with open('bahan.txt', 'r', encoding='utf-8') as f:
    teks = f.read()

q = TextQuilter(teks, kapasitas_memori=5, panjang_patch=7)

data = {
    "tokens": q.tokens,
    "patch_map": q.patch_map,
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f)
