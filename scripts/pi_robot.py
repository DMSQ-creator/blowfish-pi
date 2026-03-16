import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests
import json
import os
import time
import re
import subprocess

# ==========================================
# Pi Network 全自动同步机器人 (scripts/pi_robot.py)
# - 抓取 minepi.com 官方博客
# - 自动翻译为中文
# - 生成静态 HTML 博文页面
# - 更新博客列表页
# - 通过 Telegram 通知 Andy
# ==========================================

BLOG_URL = "https://minepi.com/blog/"
NEWS_FILE = "data/news.json"
BLOG_DIR = "blog"
BLOG_LIST_PAGE = "blog.html"
TG_BOT_TOKEN = "8744995411:AAHRiUzEGJuDFQvbJfTh0kMU_o1o60Wttl0"
TG_CHAT_ID = "8190223294"  # Andy 的 Telegram ID

# CLI-API 本地翻译接口（与 OpenClaw 同机部署）
TRANSLATE_API_URL = "http://127.0.0.1:8317/v1/chat/completions"
TRANSLATE_API_KEY = "lKT7AW_-0AU4yCJ1OWZnw3LE3F2OZPEH"
TRANSLATE_MODEL = "gemini-3-flash"

# ==========================================
# HTML 博文模板
# ==========================================
ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Pi Network 中文网</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #0f021a; color: white; line-height: 1.8; font-family: sans-serif; }}
        .text-pi-gold {{ background: linear-gradient(90deg, #f4af47 0%, #fab44b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .prose p {{ margin-bottom: 1.8rem; font-size: 1.15rem; color: #cbd5e1; text-align: justify; }}
        .prose h2 {{ font-size: 2.2rem; font-weight: 900; margin: 4rem 0 2rem; color: #f4af47; }}
        .prose h3 {{ font-size: 1.6rem; font-weight: 700; margin: 3rem 0 1.5rem; color: #e2e8f0; }}
        .prose blockquote {{ border-left: 4px solid #f4af47; padding-left: 1.5rem; margin: 2rem 0; font-style: italic; color: #f4af47; font-weight: bold; }}
    </style>
</head>
<body class="min-h-screen">
    <nav class="p-6 border-b border-white/5 bg-[#0f021a]/80 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <a href="../blog.html" class="text-gray-400 hover:text-white font-bold">← 返回社区资讯</a>
            <span class="text-[#f4af47] font-black uppercase">Official Announcement</span>
        </div>
    </nav>
    <main class="max-w-3xl mx-auto py-20 px-6">
        {hero_image}
        <h1 class="text-5xl md:text-7xl font-black mb-4 tracking-tighter leading-tight">{headline}</h1>
        <p class="text-gray-500 mb-10">{date}</p>
        <div class="prose max-w-none">
            {content}
        </div>
    </main>
</body>
</html>"""


def send_tg_notification(title, slug):
    """发送 Telegram 通知"""
    msg = (
        f"🔔 *Pi 币中文网 - 自动发布成功!*\n\n"
        f"📝 *标题*: {title}\n"
        f"🔗 *链接*: https://pibizh.com/blog/{slug}.html\n\n"
        f"大管家报告：最新官方资讯已全量搬运并汉化完毕！"
    )
    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(api_url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        print("[*] Telegram 通知已发送。")
    except Exception as e:
        print(f"[!] Telegram 通知发送失败: {e}")


def translate_text(text, context="Pi Network 官方博客文章"):
    """使用本地 CLI-API 翻译英文为中文"""
    prompt = (
        f"你是专业的区块链/加密货币中英翻译专家。请将以下 Pi Network 官方博客内容翻译为流畅的简体中文。\n"
        f"要求：\n"
        f"- 保持专业术语准确（Pioneer=先锋, Mainnet=主网, KYC=KYC, Node=节点, DApp=DApp）\n"
        f"- 翻译要自然流畅，不要机翻感\n"
        f"- 保留所有 HTML 标签原样不动\n"
        f"- 只输出翻译结果，不要加任何解释\n\n"
        f"原文：\n{text}"
    )
    try:
        resp = requests.post(
            TRANSLATE_API_URL,
            headers={"Authorization": f"Bearer {TRANSLATE_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": TRANSLATE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 8192,
            },
            timeout=120,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"[!] 翻译 API 返回 {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[!] 翻译失败: {e}")
        return None


def fetch_article_content(url):
    """抓取单篇文章的完整内容"""
    try:
        r = crequests.get(url, impersonate="chrome120", timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        # 尝试多种选择器获取正文
        article = soup.find("article") or soup.find("div", class_="entry-content") or soup.find("main")
        if not article:
            print(f"[!] 无法解析文章内容: {url}")
            return None, None, None

        # 提取标题
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # 提取日期
        date_tag = soup.find("time") or soup.find(class_=re.compile(r"date|time|published"))
        date_str = date_tag.get_text(strip=True) if date_tag else ""

        # 提取 hero image
        hero_img = None
        first_img = article.find("img")
        if first_img and first_img.get("src"):
            hero_img = first_img["src"]

        # 提取正文 HTML（去除脚本和样式）
        for tag in article.find_all(["script", "style", "nav"]):
            tag.decompose()

        content_html = str(article)
        return title, date_str, content_html, hero_img
    except Exception as e:
        print(f"[!] 抓取文章失败 {url}: {e}")
        return None, None, None, None


def generate_blog_html(title_cn, date_str, content_cn, hero_img, slug):
    """生成博文 HTML 文件"""
    hero_html = ""
    if hero_img:
        hero_html = f'<div class="mb-12 rounded-[40px] overflow-hidden"><img src="{hero_img}" class="w-full" alt="{title_cn}"></div>'

    # 简化标题用于 headline（可做分行处理）
    headline = title_cn
    if len(title_cn) > 20:
        mid = len(title_cn) // 2
        # 找最近的标点或空格断行
        for i in range(mid, min(mid + 10, len(title_cn))):
            if title_cn[i] in "：:，, 、":
                headline = f'{title_cn[:i+1]}<br><span class="text-pi-gold italic">{title_cn[i+1:]}</span>'
                break

    html = ARTICLE_TEMPLATE.format(
        title=title_cn,
        headline=headline,
        date=date_str,
        hero_image=hero_html,
        content=content_cn,
    )

    filepath = os.path.join(BLOG_DIR, f"{slug}.html")
    os.makedirs(BLOG_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[*] 已生成博文: {filepath}")
    return filepath


def update_blog_list(news_data):
    """更新 blog.html 博客列表页（如果存在）"""
    if not os.path.exists(BLOG_LIST_PAGE):
        print("[*] blog.html 不存在，跳过列表更新")
        return

    try:
        with open(BLOG_LIST_PAGE, "r", encoding="utf-8") as f:
            html = f.read()

        # 检查是否已包含该文章的链接
        for item in news_data:
            slug = item["id"]
            link = f'blog/{slug}.html'
            if link not in html:
                print(f"[*] 提示：blog.html 中未找到 {link} 的链接，可能需要手动更新列表页")
    except Exception as e:
        print(f"[!] 检查 blog.html 失败: {e}")


def fetch_latest_posts():
    """抓取 minepi.com 博客首页，获取最新文章列表"""
    print("[*] 正在巡逻 MinePi.com 官网博客...")
    try:
        r = crequests.get(BLOG_URL, impersonate="chrome120", timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.find_all("article")

        latest_items = []
        for art in articles:
            title_tag = art.find("h3", class_="title") or art.find("h2") or art.find("h3")
            link_tag = None
            if title_tag:
                link_tag = title_tag.find("a")
            if not link_tag:
                link_tag = art.find("a")

            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                # 提取 slug
                slug = href.rstrip("/").split("/")[-1]
                # 构建完整 URL
                full_url = href if href.startswith("http") else f"https://minepi.com{href}"
                latest_items.append(
                    {
                        "title": title_tag.get_text(strip=True) if title_tag else "Untitled",
                        "url_slug": slug,
                        "full_url": full_url,
                    }
                )
        print(f"[*] 发现 {len(latest_items)} 篇文章")
        return latest_items
    except Exception as e:
        print(f"[!] 抓取失败: {e}")
        return []


def run_sync():
    """主同步逻辑"""
    # 读取旧数据防止重复
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
            old_ids = [item["id"] for item in old_data]
    else:
        old_data = []
        old_ids = []

    latest_posts = fetch_latest_posts()

    new_count = 0
    for post in latest_posts:
        if post["url_slug"] in old_ids:
            continue

        print(f"[*] 发现新文章: {post['title']}")
        print(f"[*] 正在抓取全文: {post['full_url']}")

        # 1. 抓取原文
        result = fetch_article_content(post["full_url"])
        if result is None or result[0] is None:
            print(f"[!] 跳过无法解析的文章: {post['title']}")
            continue

        title_en, date_str, content_html, hero_img = result

        # 2. 翻译标题
        print("[*] 正在翻译标题...")
        title_cn = translate_text(title_en, "文章标题")
        if not title_cn:
            title_cn = post["title"]  # fallback

        # 清理翻译结果中可能的引号
        title_cn = title_cn.strip("\"'`")

        # 3. 翻译正文
        print("[*] 正在翻译正文（可能需要较长时间）...")
        content_cn = translate_text(content_html, "文章正文，保留所有 HTML 标签")
        if not content_cn:
            print("[!] 翻译失败，使用原文")
            content_cn = content_html

        # 4. 生成摘要
        excerpt_cn = translate_text(post["title"] + " - 请根据标题生成一句 50 字以内的中文摘要", "摘要")
        if not excerpt_cn or len(excerpt_cn) > 200:
            # 从翻译内容提取前100字作为摘要
            text_only = BeautifulSoup(content_cn, "html.parser").get_text()
            excerpt_cn = text_only[:100].strip() + "..."

        # 5. 生成 HTML 文件
        generate_blog_html(title_cn, date_str, content_cn, hero_img, post["url_slug"])

        # 6. 更新 news.json
        new_entry = {
            "id": post["url_slug"],
            "date": date_str or time.strftime("%Y-%m-%d"),
            "title": title_cn,
            "excerpt": excerpt_cn,
            "content": content_cn[:500] + "...",  # 只存前500字
        }
        old_data.insert(0, new_entry)

        # 7. 发送通知
        send_tg_notification(title_cn, post["url_slug"])

        new_count += 1
        time.sleep(2)  # 防止 API 限速

    # 保存更新后的 news.json
    if new_count > 0:
        os.makedirs(os.path.dirname(NEWS_FILE) or ".", exist_ok=True)
        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        print(f"[*] 已更新 news.json，新增 {new_count} 篇")
        update_blog_list(old_data)
    else:
        print("[*] 暂无新内容，继续待命。")


if __name__ == "__main__":
    run_sync()
