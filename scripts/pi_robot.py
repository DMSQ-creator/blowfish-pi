import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests
from deep_translator import GoogleTranslator
import json
import os
import time
import re

# ==========================================
# Pi Network 全自动同步机器人 (scripts/pi_robot.py)
# - 抓取 minepi.com 官方博客
# - 自动翻译为中文（Google Translate）
# - 生成静态 HTML 博文页面
# - 自动更新 blog.html 列表页
# - 通过 Telegram 通知 Andy
# ==========================================

BLOG_URL = "https://minepi.com/blog/"
NEWS_FILE = "data/news.json"
BLOG_DIR = "blog"
BLOG_LIST_PAGE = "blog.html"
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "8190223294")

# 检查 token 是否配置
if not TG_BOT_TOKEN:
    print("[!] 警告：TG_BOT_TOKEN 环境变量未设置，Telegram 通知已禁用")
IMGBB_API_KEY = "0e0e8b6212d394dd3a99aac94e107c7c"  # imgbb 图床 API Key

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
        .prose img {{ border-radius: 1.5rem; margin: 2rem 0; }}
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
        <h1 class="text-4xl md:text-6xl font-black mb-4 tracking-tighter leading-tight">{title}</h1>
        <p class="text-gray-500 mb-10">{date}</p>
        <div class="prose max-w-none">
            {content}
        </div>
    </main>
</body>
</html>"""

# blog.html 列表卡片模板
BLOG_CARD_TEMPLATE = """
            <!-- {slug} -->
            <a href="blog/{slug}.html" class="blog-card block">
                <div class="text-[#f4af47] font-bold mb-4">{date} · {category}</div>
                <h2 class="text-3xl font-bold mb-4">{title}</h2>
                <p class="text-gray-500 mb-6 text-sm">{excerpt}</p>
            </a>"""


def send_tg_notification(title, slug):
    """发送 Telegram 通知"""
    if not TG_BOT_TOKEN:
        print("[!] TG_BOT_TOKEN 为空，跳过通知")
        return
    
    msg = (
        f"🔔 *Pi 币中文网 - 自动发布成功!*\n\n"
        f"📝 *标题*: {title}\n"
        f"🔗 *链接*: https://pibizh.com/blog/{slug}.html\n\n"
        f"大管家报告：最新官方资讯已全量搬运并汉化完毕！"
    )
    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(api_url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code == 200:
            print("[✓] Telegram 通知已发送。")
        else:
            print(f"[!] Telegram 通知失败: HTTP {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"[!] Telegram 通知发送失败: {e}")


def translate_text(text, max_retries=2):
    """使用 Google Translate 翻译英文为简体中文"""
    if not text or len(text.strip()) < 3:
        return text
    for attempt in range(max_retries + 1):
        try:
            translator = GoogleTranslator(source='en', target='zh-CN')
            result = translator.translate(text.strip())
            if result:
                return result
            print(f"[!] Google Translate 返回空结果")
            return None
        except Exception as e:
            print(f"[!] 翻译失败 (尝试 {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(3)
    return None


def clean_html_content(raw_html):
    """清理从 minepi.com 抓取的 HTML，提取纯文本段落"""
    soup = BeautifulSoup(raw_html, "html.parser")

    # 移除不需要的标签（保留 iframe 用于视频嵌入）
    for tag in soup.find_all(["script", "style", "nav", "noscript"]):
        tag.decompose()

    # 提取结构化内容
    paragraphs = []
    images = []
    videos = []  # 保存视频嵌入（YouTube iframe 等）

    for elem in soup.find_all(["h2", "h3", "p", "img", "blockquote", "ul", "ol", "iframe", "figure"]):
        if elem.name == "iframe":
            src = elem.get("src", "") or elem.get("data-src", "")
            # 只保留 YouTube/视频 iframe
            if src and ("youtube" in src or "youtu.be" in src or "vimeo" in src):
                # 确保是 embed 格式
                if "youtube.com/watch" in src:
                    video_id = src.split("v=")[-1].split("&")[0]
                    src = f"https://www.youtube.com/embed/{video_id}"
                videos.append(src)
                paragraphs.append({"type": "video", "text": src})
        elif elem.name == "figure":
            # figure 可能包含图片或视频
            img = elem.find("img")
            if img:
                src = img.get("src", "") or img.get("data-src", "") or img.get("nitro-lazy-src", "") or img.get("data-lazy-src", "")
                if src and src.startswith("http"):
                    images.append(src)
                    paragraphs.append({"type": "img", "text": src})
        elif elem.name == "img":
            src = elem.get("src", "") or elem.get("data-src", "") or elem.get("nitro-lazy-src", "") or elem.get("data-lazy-src", "") or elem.get("data-original", "")
            if src and src.startswith("http") and src not in images:
                images.append(src)
                paragraphs.append({"type": "img", "text": src})
        elif elem.name in ("h2", "h3"):
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                paragraphs.append({"type": elem.name, "text": text})
        elif elem.name == "blockquote":
            text = elem.get_text(strip=True)
            if text:
                paragraphs.append({"type": "blockquote", "text": text})
        elif elem.name in ("ul", "ol"):
            items = [li.get_text(strip=True) for li in elem.find_all("li") if li.get_text(strip=True)]
            if items:
                paragraphs.append({"type": "list", "text": "\n".join(f"• {item}" for item in items)})
        elif elem.name == "p":
            text = elem.get_text(strip=True)
            if text and len(text) > 10:  # 过滤太短的段落
                paragraphs.append({"type": "p", "text": text})

    return paragraphs, images


def build_chinese_html(paragraphs_cn, images, hero_img):
    """将翻译后的段落重建为干净的 HTML"""
    html_parts = []

    for para in paragraphs_cn:
        ptype = para.get("type", "p")
        text = para.get("text", "")
        if not text:
            continue

        if ptype == "h2":
            html_parts.append(f"<h2>{text}</h2>")
        elif ptype == "h3":
            html_parts.append(f"<h3>{text}</h3>")
        elif ptype == "blockquote":
            html_parts.append(f"<blockquote>{text}</blockquote>")
        elif ptype == "list":
            items = text.split("\n")
            li_items = "".join(f"<li>{item.lstrip('• ').strip()}</li>" for item in items if item.strip())
            html_parts.append(f"<ul class='list-disc pl-6 my-4 text-gray-300 space-y-2'>{li_items}</ul>")
        elif ptype == "img":
            html_parts.append(f'<img src="{text}" class="w-full rounded-2xl my-8" />')
        elif ptype == "video":
            html_parts.append(
                f'<div class="my-8 rounded-2xl overflow-hidden aspect-video">'
                f'<iframe src="{text}" class="w-full h-full" frameborder="0" '
                f'allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">'
                f'</iframe></div>'
            )
        else:
            html_parts.append(f"<p>{text}</p>")

    return "\n            ".join(html_parts)


def upload_to_imgbb(image_url):
    """将图片上传到 imgbb 图床，返回永久链接；失败则返回原 URL"""
    try:
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": image_url},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                new_url = data["data"]["url"]
                print(f"[✓] 图床上传成功: {image_url[:60]}... -> {new_url}")
                return new_url
        print(f"[!] imgbb 上传失败 (HTTP {resp.status_code}): {image_url[:60]}")
    except Exception as e:
        print(f"[!] imgbb 上传异常: {e}")
    return image_url  # 失败时回退到原始链接


def fetch_article_content(url):
    """抓取单篇文章的完整内容"""
    try:
        r = crequests.get(url, impersonate="chrome120", timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        article = soup.find("article") or soup.find("div", class_="entry-content") or soup.find("main")
        if not article:
            print(f"[!] 无法解析文章内容: {url}")
            return None, None, None, None

        # 提取标题
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # 提取日期
        date_tag = soup.find("time") or soup.find(class_=re.compile(r"date|time|published"))
        date_str = date_tag.get_text(strip=True) if date_tag else ""

        # 提取 hero image（文章首图）
        hero_img = None
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            hero_img = og_img["content"]
        else:
            first_img = article.find("img")
            if first_img:
                hero_img = first_img.get("src") or first_img.get("data-src") or first_img.get("nitro-lazy-src")

        # 清理并提取段落
        paragraphs, images = clean_html_content(str(article))

        return title, date_str, paragraphs, images, hero_img
    except Exception as e:
        print(f"[!] 抓取文章失败 {url}: {e}")
        return None, None, None, None, None


def update_blog_list_page(new_entry):
    """在 blog.html 中插入新文章卡片"""
    if not os.path.exists(BLOG_LIST_PAGE):
        print("[!] blog.html 不存在，跳过列表更新")
        return

    try:
        with open(BLOG_LIST_PAGE, "r", encoding="utf-8") as f:
            html = f.read()

        slug = new_entry["id"]
        if f'blog/{slug}.html' in html:
            print(f"[*] blog.html 已包含 {slug}，跳过")
            return

        # 生成新卡片
        card = BLOG_CARD_TEMPLATE.format(
            slug=slug,
            date=new_entry["date"].replace("-", "."),
            category="官方公告",
            title=new_entry["title"],
            excerpt=new_entry["excerpt"][:80],
        )

        # 在 blog-grid 开头插入（第一个 <!-- 之前）
        insert_marker = '<div id="blog-grid" class="grid gap-10">'
        if insert_marker in html:
            html = html.replace(insert_marker, insert_marker + card, 1)

            with open(BLOG_LIST_PAGE, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[*] blog.html 已更新，插入了 {slug}")
        else:
            print("[!] 找不到 blog-grid 插入点")

    except Exception as e:
        print(f"[!] 更新 blog.html 失败: {e}")


def generate_blog_html(title_cn, date_str, content_html, hero_img, slug):
    """生成博文 HTML 文件"""
    hero_html = ""
    if hero_img and hero_img.startswith("http"):
        hero_html = f'<div class="mb-12 rounded-[40px] overflow-hidden"><img src="{hero_img}" class="w-full" alt="{title_cn}"></div>'

    html = ARTICLE_TEMPLATE.format(
        title=title_cn,
        date=date_str,
        hero_image=hero_html,
        content=content_html,
    )

    filepath = os.path.join(BLOG_DIR, f"{slug}.html")
    os.makedirs(BLOG_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[*] 已生成博文: {filepath}")
    return filepath


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
                slug = href.rstrip("/").split("/")[-1]
                full_url = href if href.startswith("http") else f"https://minepi.com{href}"
                latest_items.append({
                    "title": title_tag.get_text(strip=True) if title_tag else "Untitled",
                    "url_slug": slug,
                    "full_url": full_url,
                })
        print(f"[*] 发现 {len(latest_items)} 篇文章")
        return latest_items
    except Exception as e:
        print(f"[!] 抓取失败: {e}")
        return []


def run_sync():
    """主同步逻辑"""
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

        print(f"\n[*] ===== 处理新文章: {post['title']} =====")
        print(f"[*] 正在抓取全文: {post['full_url']}")

        # 1. 抓取原文
        result = fetch_article_content(post["full_url"])
        if result is None or result[0] is None:
            print(f"[!] 跳过无法解析的文章: {post['title']}")
            continue

        title_en, date_str, paragraphs, images, hero_img = result
        if not paragraphs:
            print(f"[!] 文章内容为空，跳过: {title_en}")
            continue

        print(f"[*] 提取到 {len(paragraphs)} 个段落, {len(images)} 张图片")

        # 2. 翻译标题
        print("[*] 正在翻译标题...")
        title_cn = translate_text(title_en)
        if not title_cn:
            print("[!] 标题翻译失败，使用原文")
            title_cn = post["title"]
        title_cn = title_cn.strip("\"'`\n")
        print(f"[*] 中文标题: {title_cn}")

        # 3. 分批翻译段落（每批合并5段以减少API调用，img/video 类型跳过翻译）
        print("[*] 正在翻译正文...")
        translated_paragraphs = []
        # 先把不需要翻译的段落分离出来
        text_paragraphs = [(i, p) for i, p in enumerate(paragraphs) if p["type"] not in ("img", "video")]
        
        batch_size = 5
        translated_text = {}
        for batch_start in range(0, len(text_paragraphs), batch_size):
            batch = text_paragraphs[batch_start:batch_start+batch_size]
            batch_text = ""
            for j, (orig_idx, para) in enumerate(batch):
                marker = f"[{para['type'].upper()}]"
                batch_text += f"{marker} {para['text']}\n\n"

            translated = translate_text(batch_text)
            if translated:
                lines = [l.strip() for l in translated.split("\n") if l.strip()]
                para_idx = 0
                for line in lines:
                    if para_idx >= len(batch):
                        break
                    clean_line = re.sub(r'^\[(H2|H3|P|BLOCKQUOTE|LIST)\]\s*', '', line)
                    if clean_line:
                        orig_idx = batch[para_idx][0]
                        translated_text[orig_idx] = clean_line
                        para_idx += 1
            else:
                print(f"[!] 第 {batch_start//batch_size+1} 批翻译失败，使用原文")

            time.sleep(1)  # 防止限速

        # 按原顺序重组（img/video 保留原文，其他用翻译）
        for i, para in enumerate(paragraphs):
            if para["type"] in ("img", "video"):
                translated_paragraphs.append(para)
            else:
                text = translated_text.get(i, para["text"])  # 翻译失败则用原文
                translated_paragraphs.append({"type": para["type"], "text": text})

        # 4. 上传图片到图床（hero + 内容图片）
        all_imgs = [p["text"] for p in translated_paragraphs if p["type"] == "img"]
        print(f"[*] 正在上传 {len(all_imgs)+1} 张图片到 imgbb 图床...")
        hero_img = upload_to_imgbb(hero_img) if hero_img else hero_img
        # 替换 paragraphs 里的图片 URL
        for p in translated_paragraphs:
            if p["type"] == "img":
                p["text"] = upload_to_imgbb(p["text"])

        # 5. 构建干净的中文 HTML
        content_html = build_chinese_html(translated_paragraphs, images, hero_img)

        # 6. 生成摘要
        first_p = next((p["text"] for p in translated_paragraphs if p["type"] == "p"), "")
        excerpt_cn = first_p[:100] + "..." if len(first_p) > 100 else first_p

        # 7. 生成 HTML 文件
        generate_blog_html(title_cn, date_str or time.strftime("%Y-%m-%d"), content_html, hero_img, post["url_slug"])

        # 8. 更新 news.json
        new_entry = {
            "id": post["url_slug"],
            "date": date_str or time.strftime("%Y-%m-%d"),
            "title": title_cn,
            "excerpt": excerpt_cn,
        }
        old_data.insert(0, new_entry)

        # 9. 更新 blog.html 列表页
        update_blog_list_page(new_entry)

        # 10. 发送通知
        send_tg_notification(title_cn, post["url_slug"])

        new_count += 1
        time.sleep(3)  # 文章间间隔

    # 保存 news.json
    if new_count > 0:
        os.makedirs(os.path.dirname(NEWS_FILE) or ".", exist_ok=True)
        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        print(f"\n[*] 完成！共处理 {new_count} 篇新文章")
    else:
        print("[*] 暂无新内容，继续待命。")


if __name__ == "__main__":
    run_sync()
