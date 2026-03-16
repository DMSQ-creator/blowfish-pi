import requests
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://minepi.com/'
}

urls = {
    'nicolas.jpg': 'https://minepi.com/wp-content/uploads/2022/11/nicolas-kokkalis.jpg',
    'chengdiao.jpg': 'https://minepi.com/wp-content/uploads/2022/11/chengdiao-fan.jpg',
    'hero-banner.jpg': 'https://minepi.com/wp-content/uploads/2026/03/Celebrating-the-Pioneer-Community-3-900x600.jpg'
}

os.makedirs('static/img', exist_ok=True)

for name, url in urls.items():
    print(f"Downloading {name}...")
    r = requests.get(url, headers=headers)
    if r.status_code == 200 and len(r.content) > 2000:
        with open(f'static/img/{name}', 'wb') as f:
            f.write(r.content)
        print(f"Success: {name} ({len(r.content)} bytes)")
    else:
        print(f"Failed: {name} (Status: {r.status_code}, Size: {len(r.content)})")
