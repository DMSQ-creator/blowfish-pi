#!/usr/bin/env python3
"""
pibizh.com 静态站构建脚本 v2

核心原则：内容与模板彻底分离
- _templates/ : 公共模板（head/nav/footer）—— 只管外壳
- _content/   : 纯正文片段（每个页面一个 .html）—— 只管内容
- _pages/pages.yml : 页面元数据（title/description/body_class）
- build.py    : 纯正向组装，永不从完整 HTML 反向提取

工作流：
  编辑内容 → _content/xxx.html
  编辑外壳 → _templates/head.html, nav.html, footer.html
  编辑元数据 → _pages/pages.yml
  构建 → python3 build.py
  新建页面 → 创建 _content/xxx.html + 在 pages.yml 加一条
"""

import os
import re
from datetime import datetime
from html import escape, unescape
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "_templates"
PAGES_DIR = BASE_DIR / "_pages"
CONTENT_DIR = BASE_DIR / "_content"
DIST_DIR = BASE_DIR  # 输出到根目录
BLOG_DIR = BASE_DIR / "blog"

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


def plain_text(value):
    """将一小段 HTML 转成适合资讯卡片的纯文本。"""
    value = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', unescape(value)).strip()


def parse_blog_date(value):
    """兼容机器人历史上写入的三种日期格式。"""
    value = plain_text(value)
    for fmt in ('%Y-%m-%d', '%Y.%m.%d'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    match = re.fullmatch(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})', value)
    if match and match.group(1).lower() in MONTHS:
        return datetime(int(match.group(3)), MONTHS[match.group(1).lower()], int(match.group(2)))

    match = re.fullmatch(r'(20\d{2})年(\d{1,2})月(\d{1,2})日', value)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def load_blog_posts():
    """从已生成的中文博文中读取标题、日期和摘要，并按发布日期倒序。"""
    posts = []
    for path in BLOG_DIR.glob('*.html'):
        html = path.read_text(encoding='utf-8', errors='ignore')
        main_match = re.search(r'<main\b[^>]*>(.*?)</main>', html, re.I | re.S)
        main_html = main_match.group(1) if main_match else html

        title_match = re.search(r'<h1\b[^>]*>(.*?)</h1>', main_html, re.I | re.S)
        date_match = re.search(
            r'<p\b[^>]*class=["\'][^"\']*text-gray-500[^"\']*mb-10[^"\']*["\'][^>]*>(.*?)</p>',
            main_html,
            re.I | re.S,
        )
        prose_match = re.search(r'<div\b[^>]*class=["\'][^"\']*prose[^"\']*["\'][^>]*>(.*?)</div>', main_html, re.I | re.S)
        excerpt_match = re.search(r'<p\b[^>]*>(.*?)</p>', prose_match.group(1), re.I | re.S) if prose_match else None

        title = plain_text(title_match.group(1)) if title_match else ''
        published = parse_blog_date(date_match.group(1)) if date_match else None
        excerpt = plain_text(excerpt_match.group(1)) if excerpt_match else title
        if not title or not published:
            print(f"  WARN: blog/{path.name} 缺少可识别的标题或日期，不加入资讯列表")
            continue

        posts.append({
            'slug': path.stem,
            'title': title,
            'published': published,
            'excerpt': excerpt[:150],
        })

    posts.sort(key=lambda item: (item['published'], item['slug']), reverse=True)
    return posts


def render_blog_cards(posts):
    """生成全中文日期的静态资讯卡片。"""
    cards = []
    for post in posts:
        date_cn = f"{post['published'].year}年{post['published'].month}月{post['published'].day}日"
        cards.append(f'''            <a href="blog/{post['slug']}.html" class="blog-card block">
                <div class="bg-white/5 rounded-[24px] overflow-hidden border border-white/10 hover:border-[#f4af47]/40 transition-all hover:shadow-lg hover:shadow-[#f4af47]/10 h-full">
                    <div class="p-6">
                        <div class="text-[#f4af47] font-bold mb-2 text-sm">{date_cn} · 官方公告</div>
                        <h2 class="text-xl font-bold mb-3 text-white leading-snug">{escape(post['title'])}</h2>
                        <p class="text-gray-400 text-sm line-clamp-2">{escape(post['excerpt'])}</p>
                    </div>
                </div>
            </a>''')
    return '\n'.join(cards)


BLOG_POSTS = load_blog_posts()

# ─── 加载模板 ───
def load_template(name):
    path = TEMPLATES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

HEAD_TMPL = load_template("head.html")
NAV_TMPL = load_template("nav.html")
FOOTER_TMPL = load_template("footer.html")
ARTICLE_STYLE_TMPL = load_template("article-style.html")


def sync_blog_article_styles():
    """把统一正文样式同步进所有已生成博文；重复构建保持幂等。"""
    style_pattern = re.compile(
        r'(?:<style\s+id=["\']article-content-styles["\']>.*?</style>|'
        r'<link\s+id=["\']article-content-styles["\'][^>]*>)\s*',
        re.I | re.S,
    )
    date_pattern = re.compile(
        r'(<p\b[^>]*class=["\'][^"\']*text-gray-500[^"\']*mb-10[^"\']*["\'][^>]*>)(.*?)(</p>)',
        re.I | re.S,
    )

    def localize_date(match):
        published = parse_blog_date(match.group(2))
        if not published:
            return match.group(0)
        date_cn = f'{published.year}年{published.month}月{published.day}日'
        return f'{match.group(1)}{date_cn}{match.group(3)}'

    updated = 0
    for path in BLOG_DIR.glob('*.html'):
        html = path.read_text(encoding='utf-8', errors='ignore')
        without_old_style = style_pattern.sub('', html)
        without_old_style = date_pattern.sub(localize_date, without_old_style)
        if '</head>' not in without_old_style:
            print(f"  WARN: blog/{path.name} 缺少 </head>，无法同步正文样式")
            continue
        refreshed = without_old_style.replace('</head>', ARTICLE_STYLE_TMPL + '\n</head>', 1)
        if refreshed != html:
            path.write_text(refreshed, encoding='utf-8')
            updated += 1
    print(f"Synced article styles to {updated} blog pages")

# ─── 加载页面元数据 ───
def load_pages_yml():
    path = PAGES_DIR / "pages.yml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

# ─── 广告插入 ───
def insert_ads(page_content, page_file):
    """在内容页插入 AdSense 广告（列表页和特殊页不加）"""
    listing_pages = {'index.html', 'blog.html', 'price.html', 'community.html'}
    no_ad_pages = {'404.html', 'reg.html', 'search.html', 'technical-whitepaper.html'}
    if page_file in listing_pages or page_file in no_ad_pages:
        return page_content

    # 文章中间广告：插在第2个 </section> 后
    in_article_ad = '''
<!-- AdSense 文章中间广告 -->
<ins class="adsbygoogle"
     style="display:block; text-align:center;"
     data-ad-layout="in-article"
     data-ad-format="fluid"
     data-ad-client="ca-pub-4800945095334481"
     data-ad-slot="8883735919"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>'''

    sections = list(re.finditer(r'</section>', page_content))
    if len(sections) >= 2:
        pos = sections[1].end()
    elif len(sections) >= 1:
        pos = sections[0].end()
    else:
        pos = len(page_content) // 2
        for tag in ['</div>', '</p>', '</h2>', '</h3>']:
            snap = page_content.find(tag, pos)
            if snap != -1:
                pos = snap + len(tag)
                break
    page_content = page_content[:pos] + in_article_ad + page_content[pos:]
    return page_content

def get_footer_ads(page_file):
    """返回页面底部广告 HTML（特定页面不加）"""
    no_ad_pages = {'404.html', 'reg.html', 'search.html', 'technical-whitepaper.html'}
    if page_file in no_ad_pages:
        return ''
    return '''    <!-- 页面底部广告 -->
    <section class="py-8 px-6 border-t border-white/5">
        <div class="container mx-auto max-w-4xl">
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-4800945095334481"
     data-ad-slot="9568510432"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
        </div>
    </section>
'''

# ─── 构建单个页面 ───
def build_page(page_name, meta):
    """从 _content/ 读取内容片段，与模板组装输出完整 HTML"""
    page_file = f"{page_name}.html"
    content_path = CONTENT_DIR / page_file

    if not content_path.exists():
        print(f"  SKIP: {page_file} (no _content/{page_file})")
        return None

    # 1. 读取纯内容片段
    with open(content_path, "r", encoding="utf-8") as f:
        page_content = f.read().strip()

    # 资讯列表在构建时从 blog/*.html 正向生成，避免机器人插入顺序错乱。
    if page_file == 'blog.html':
        page_content = page_content.replace('{{BLOG_CARDS}}', render_blog_cards(BLOG_POSTS))
    elif page_file == 'index.html':
        page_content = page_content.replace('{{HOME_BLOG_CARDS}}', render_blog_cards(BLOG_POSTS[:10]))

    if not page_content:
        print(f"  SKIP: {page_file} (empty content)")
        return None

    # 🚨 内容合规检查：_content/ 里不允许出现外壳元素
    forbidden = [
        ('<head', '_content/ 不得包含 <head>，head 由模板注入'),
        ('</head>', '_content/ 不得包含 </head>，head 由模板注入'),
        ('<!-- 导航栏', '_content/ 不得包含导航栏，nav 由模板注入'),
        ('<footer', '_content/ 不得包含 <footer>，footer 由模板注入'),
        ('© 2026 PI NETWORK', '_content/ 不得包含页脚内容，footer 由模板注入'),
    ]
    for pattern, msg in forbidden:
        if pattern in page_content:
            print(f"  🚨 RULE VIOLATION: {page_file} → {msg}")
            print(f"     请只放 <main> 内的正文内容，外壳由 _templates/ 提供")
            return None

    # 2. 从 pages.yml 获取元数据
    title = meta.get('title', f'{page_name} | 派币中文网')
    desc = meta.get('description', '')
    body_class = meta.get('body_class', None)

    # body_extra: 首页不需要 pt-24，其他页面需要
    if body_class == '':
        body_extra = ''
    else:
        body_extra = ' pt-24'

    canonical = f'https://pibizh.com/{page_file}'
    head_extra = f'''    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="/static/favicon.png">
    <meta property="og:locale" content="zh_CN">'''

    # 3. 插入广告
    page_content = insert_ads(page_content, page_file)

    # 4. 组装
    head_html = HEAD_TMPL.replace("{{HEAD_EXTRA}}", head_extra).replace("{{BODY_CLASS}}", body_extra)
    footer_ads = get_footer_ads(page_file)

    full_html = head_html + "\n" + NAV_TMPL + "\n    " + page_content + "\n" + footer_ads + FOOTER_TMPL

    # 清理重复的 </body></html>
    full_html = re.sub(r'(</body>\s*</html>\s*)+', '</body>\n</html>', full_html)

    return full_html


# ─── 主流程 ───
def main():
    sync_blog_article_styles()
    page_metas = load_pages_yml()
    print(f"Loaded {len(page_metas)} page metas from pages.yml")

    # 扫描 _content/ 目录中的所有 .html 文件
    content_files = sorted(CONTENT_DIR.glob("*.html"))
    built = 0
    skipped = 0

    for content_path in content_files:
        page_name = content_path.stem  # e.g. "about"
        page_file = content_path.name  # e.g. "about.html"

        meta = page_metas.get(page_name, {})

        print(f"BUILD: {page_file}")
        html = build_page(page_name, meta)

        if html is None:
            skipped += 1
            continue

        out_path = DIST_DIR / page_file
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        built += 1

    print(f"\nDone! Built {built} pages, skipped {skipped}")
    print(f"\n💡 要新建页面：1) 创建 _content/xxx.html  2) 在 _pages/pages.yml 加一条  3) 运行 python3 build.py")


if __name__ == "__main__":
    main()
