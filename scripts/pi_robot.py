import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests
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

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
LLM_MODEL = "qwen/qwen3.5-397b-a17b"

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
    <link rel="icon" type="image/png" href="/static/favicon.png">
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


def translate_article(paragraphs, title_en, max_retries=2):
    """使用 NVIDIA Qwen3.5 一次性翻译整篇文章，保留结构；翻译失败返回 None"""
    # 构建结构化输入，img/video 直接标记跳过
    lines = []
    for i, p in enumerate(paragraphs):
        if p["type"] in ("img", "video"):
            lines.append(f"[{i}][{p['type'].upper()}] __SKIP__")
        else:
            text = p["text"]
            # HTML 段落提取纯文本再翻译，避免标签干扰
            if text.startswith("<"):
                soup = BeautifulSoup(text, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
            lines.append(f"[{i}][{p['type'].upper()}] {text}")
    article_text = "\n".join(lines)

    prompt = f"""你是一个专业的中文翻译。请将以下 Pi Network 官方文章全文翻译为简体中文。

要求：
1. 保留每行开头的 [N][TYPE] 标记不变
2. __SKIP__ 的行不要翻译，直接输出 __SKIP__
3. 翻译要自然流畅，符合中文表达习惯
4. 保持原文的所有内容，不要删除或省略任何信息
5. 回复格式必须和输入一致，每行对应一行

标题：{title_en}

内容：
{article_text}

直接输出翻译结果，不要加任何解释或前言。"""

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                LLM_API_URL,
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 8000,
                },
                timeout=120,
            )
            if resp.status_code == 200:
                result = resp.json()["choices"][0]["message"]["content"].strip()
                # 解析结果，按行对应回去 paragraphs
                translated = []
                result_lines = {}
                for line in result.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    m = re.match(r'^\[(\d+)\]\[\w+\]\s*(.*)', line)
                    if m:
                        idx = int(m.group(1))
                        text = m.group(2).strip()
                        result_lines[idx] = text

                for i, p in enumerate(paragraphs):
                    if p["type"] in ("img", "video"):
                        translated.append(p)
                    else:
                        text = result_lines.get(i, p["text"])  # 找不到则用原文
                        if text == "__SKIP__":
                            text = p["text"]
                        translated.append({"type": p["type"], "text": text})

                # 中文检测：段落中少于 5% 字符为中文则判定翻译失败
                chinese_count = sum(
                    sum(1 for c in tp["text"] if '\u4e00' <= c <= '\u9fff')
                    for tp in translated if tp["type"] not in ("img", "video")
                )
                total_chars = sum(
                    len(tp["text"])
                    for tp in translated if tp["type"] not in ("img", "video")
                )
                chinese_ratio = chinese_count / total_chars if total_chars > 0 else 0
                print(f"[✓] LLM 翻译完成，共 {len(translated)} 个段落，中文率 {chinese_ratio:.1%}")
                if chinese_ratio < 0.05:
                    print(f"[!] 翻译结果中文比例过低 ({chinese_count}/{total_chars})，判定为 API 失败，跳过本文")
                    return None
                return translated
            else:
                print(f"[!] LLM API 错误: HTTP {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"[!] 翻译失败 (尝试 {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(5)

    print("[!] LLM 翻译全部失败，跳过本文")
    return None  # 全部失败返回 None，调用方跳过本文


def translate_text(text, max_retries=2):
    """单段文本翻译（用于标题）"""
    if not text or len(text.strip()) < 3:
        return text
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                LLM_API_URL,
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": f"将以下英文翻译为简体中文，只输出翻译结果，不要加任何解释：\n{text}"}],
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            print(f"[!] 标题翻译失败: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[!] 标题翻译失败 (尝试 {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(3)
    return None


def _extract_video_url(iframe):
    """从 iframe 中提取视频 URL，支持多种属性"""
    # 优先用 src（标准 embed 格式）
    src = iframe.get("src", "") or iframe.get("data-src", "")
    if src and ("youtube" in src or "youtu.be" in src or "vimeo" in src):
        if "youtube.com/watch" in src:
            video_id = src.split("v=")[-1].split("&")[0]
            src = f"https://www.youtube.com/embed/{video_id}"
        return src
    # 降级检查 nitro-og-src（WPB Video Widget 等懒加载 iframe）
    nitro = iframe.get("nitro-og-src", "")
    if nitro and ("youtube" in nitro or "youtu.be" in nitro or "vimeo" in nitro):
        # nitro-og-src 可能是完整 embed URL 或 watch URL
        if "youtube.com/watch" in nitro:
            video_id = nitro.split("v=")[-1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return nitro
    return None


def _convert_internal_link(href):
    """将 minepi.com 内链转换为 pibizh.com 对应地址"""
    if not href:
        return href
    # blog 文章链接
    m = re.match(r"https://minepi\.com/blog/([\w-]+)/?", href)
    if m:
        return f"https://pibizh.com/blog/{m.group(1)}.html"
    # 固定页面链接
    if href.startswith("https://minepi.com/pi-browser"):
        return "https://pibizh.com/pi-browser"
    if href.startswith("https://minepi.com/pi-node"):
        return "https://pibizh.com/pi-node"
    if href.startswith("https://minepi.com/"):
        return href.replace("https://minepi.com", "https://pibizh.com")
    return href


def clean_html_content(raw_html):
    """清理从 minepi.com 抓取的 HTML，提取纯文本段落，内链转 pibizh.com"""
    soup = BeautifulSoup(raw_html, "html.parser")

    # 移除不需要的标签
    for tag in soup.find_all(["script", "style", "nav", "noscript"]):
        tag.decompose()

    paragraphs = []
    images = []
    seen_video_urls = set()  # 避免重复添加同一视频

    # 1. 先处理 WPB Video Widget（内含 iframe 的视频容器）
    for wpb in soup.find_all("div", class_="wpb_video_wrapper"):
        iframe = wpb.find("iframe")
        if iframe:
            video_url = _extract_video_url(iframe)
            if video_url and video_url not in seen_video_urls:
                seen_video_urls.add(video_url)
                paragraphs.append({"type": "video", "text": video_url})

    # 2. 遍历所有目标元素
    for elem in soup.find_all(["h2", "h3", "p", "img", "blockquote", "ul", "ol", "iframe", "figure"]):
        # 跳过已处理的 wpb_video_wrapper 内的元素
        if elem.name == "iframe":
            # 已在上面处理
            continue
        elif elem.name == "figure":
            img = elem.find("img")
            if img:
                src = img.get("src", "") or img.get("data-src", "") or img.get("nitro-lazy-src", "") or img.get("data-lazy-src", "")
                if src and src.startswith("http") and src not in images:
                    images.append(src)
                    paragraphs.append({"type": "img", "text": src})
        elif elem.name == "img":
            src = elem.get("src", "") or elem.get("data-src", "") or elem.get("nitro-lazy-src", "") or elem.get("data-lazy-src", "") or elem.get("data-original", "")
            if src and src.startswith("http") and src not in images:
                images.append(src)
                paragraphs.append({"type": "img", "text": src})
        elif elem.name in ("h2", "h3"):
            # 提取纯文本并转换内链
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                # 转换段落中的内链
                for a in elem.find_all("a"):
                    old_href = a.get("href", "")
                    if old_href:
                        new_href = _convert_internal_link(old_href)
                        a["href"] = new_href
                text = str(elem)  # 保留带链接的 HTML
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
            # 转换段落中的内链
            for a in elem.find_all("a"):
                old_href = a.get("href", "")
                if old_href:
                    new_href = _convert_internal_link(old_href)
                    a["href"] = new_href
            text = elem.get_text(strip=True)
            if text and len(text) > 10:
                paragraphs.append({"type": "p", "text": str(elem)})  # 保留带链接的 HTML

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
        elif ptype == "p":
            # 如果文本已是 HTML（包含内链转换后的标签），直接使用；否则包装
            if text.startswith("<"):
                html_parts.append(text)
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

        # 3. 一次性翻译整篇文章（NVIDIA Qwen3.5，保留结构）
        print("[*] 正在用 NVIDIA Qwen3.5 翻译全文...")
        translated_paragraphs = translate_article(paragraphs, title_en)
        if translated_paragraphs is None:
            print(f"[!] 文章翻译失败（API 无效或中文率不足），跳过: {title_en}")
            # 发送 Telegram 警告（使用 requests 库）
            if TG_BOT_TOKEN:
                msg = f"⚠️ *翻译失败警告*\n\n文章: {post['title']}\nSlug: {post['url_slug']}\nURL: {post['full_url']}\n\nAPI Key 可能已失效，请在 GitHub Variables 更新 LLM_API_KEY。"
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                        data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                        timeout=10
                    )
                except Exception as warn_err:
                    print(f"[!] 翻译失败警告通知失败: {warn_err}")
            continue  # 不覆盖已有 HTML，不更新 news.json

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
