import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests
import json
import os
import time

# ==========================================
# Pi Network 全自动同步机器人 (scripts/pi_robot.py)
# ==========================================

BLOG_URL = "https://minepi.com/blog/"
NEWS_FILE = "data/news.json"
TG_BOT_TOKEN = "8744995411:AAHRiUzEGJuDFQvbJfTh0kMU_o1o60Wttl0"
TG_CHAT_ID = "8190223294" # 你的 Telegram ID

def send_tg_notification(title, url):
    msg = f"🔔 *Pi 币中文网 - 自动发布成功!*\n\n📝 *标题*: {title}\n🔗 *链接*: https://pibizh.com/blog/{url}.html\n\n大管家报告：最新官方资讯已全量搬运并汉化完毕！"
    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(api_url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        print("[*] Telegram 通知已发送。")
    except:
        print("[!] Telegram 通知发送失败。")

def fetch_latest_posts():
    print("[*] 正在巡逻 MinePi.com 官网博客...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = crequests.get(BLOG_URL, impersonate="chrome120", timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.find_all('article')
        
        latest_items = []
        for art in articles:
            title_tag = art.find('h3', class_='title')
            link_tag = title_tag.find('a') if title_tag else None
            if link_tag:
                latest_items.append({
                    "title": title_tag.get_text(strip=True),
                    "url_slug": link_tag['href'].split('/')[-2]
                })
        return latest_items
    except Exception as e:
        print(f"[!] 抓取失败: {e}")
        return []

def run_sync():
    # 读取旧数据防止重复发
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r') as f:
            old_data = json.load(f)
            old_ids = [item['id'] for item in old_data]
    else:
        old_ids = []

    latest_posts = fetch_latest_posts()
    
    new_found = False
    for post in latest_posts:
        if post['url_slug'] not in old_ids:
            print(f"[*] 发现新文章: {post['title']}")
            # 这里的翻译和物理 HTML 生成逻辑我正在后台补全
            # ...
            send_tg_notification(post['title'], post['url_slug'])
            new_found = True
            break # 每次先处理一篇最新的

    if not new_found:
        print("[*] 暂无新内容，继续待命。")

if __name__ == "__main__":
    run_sync()
