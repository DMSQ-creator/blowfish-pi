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
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "_templates"
PAGES_DIR = BASE_DIR / "_pages"
CONTENT_DIR = BASE_DIR / "_content"
DIST_DIR = BASE_DIR  # 输出到根目录

# ─── 加载模板 ───
def load_template(name):
    path = TEMPLATES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

HEAD_TMPL = load_template("head.html")
NAV_TMPL = load_template("nav.html")
FOOTER_TMPL = load_template("footer.html")

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

    if not page_content:
        print(f"  SKIP: {page_file} (empty content)")
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
