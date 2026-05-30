#!/usr/bin/env python3
"""
pibizh.com 静态站构建脚本
- _templates/ 公共模板（head/nav/footer）
- _pages/*.yml 每个页面的元数据
- 每个页面的内容直接从原始 HTML 中提取
- 输出到根目录的 *.html
"""

import os
import re
import sys
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "_templates"
PAGES_DIR = BASE_DIR / "_pages"
DIST_DIR = BASE_DIR  # 输出到根目录

# Load templates
def load_template(name):
    path = TEMPLATES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

HEAD_TMPL = load_template("head.html")
NAV_TMPL = load_template("nav.html")
FOOTER_TMPL = load_template("footer.html")


def extract_page_content(html_path):
    """Extract the page-specific content (breadcrumb + sections) from an existing HTML file."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strategy: find content after the mobile menu closing </div>
    # The mobile menu ends with a </div> that has id="m-panel" as ancestor
    # After that, page content starts (breadcrumb, section, hero, etc.)
    
    # Method 1: find breadcrumb
    breadcrumb_match = re.search(
        r'<div class="container mx-auto px-6 py-3"><nav class="breadcrumb">.*?</nav></div>',
        content, re.DOTALL
    )
    
    # Method 2: find content after mobile menu script area
    # Look for </div> followed by page content (not whitespace)
    # The mobile menu div ends before content
    mobile_menu_end = content.find('id="mobile-menu"')
    if mobile_menu_end > 0:
        # Find the closing </div> of mobile-menu by counting depth
        pos = mobile_menu_end
        depth = 0
        while pos < len(content):
            open_m = re.search(r'<div[\s>]', content[pos:])
            close_m = re.search(r'</div>', content[pos:])
            if close_m is None:
                break
            if open_m and open_m.start() < close_m.start():
                depth += 1
                pos += open_m.end()
            else:
                depth -= 1
                pos += close_m.end()
                if depth == 0:
                    mobile_menu_real_end = pos
                    break
        else:
            mobile_menu_real_end = pos
    else:
        mobile_menu_real_end = 0
    
    # Method 3: find first significant content element after mobile menu
    # Look for: breadcrumb, <section, <div with content class, hero section, etc.
    after_menu = content[mobile_menu_real_end:]
    content_match = re.search(
        r'(?:<div class="container[^>]*><nav class="breadcrumb">|<section\b|<div class="(?:hero|pt-32|container mx-auto)[^"]*"|<h1\b|<main\b)',
        after_menu
    )
    
    content_start = None
    if breadcrumb_match:
        content_start = breadcrumb_match.start()
    elif content_match:
        content_start = mobile_menu_real_end + content_match.start()
    else:
        # Last resort: find first <section> anywhere after </header>
        header_end = content.find('</header>')
        if header_end > 0:
            section_after = re.search(r'<section\b|<div class="(?:hero|pt-32|container)', content[header_end:])
            if section_after:
                content_start = header_end + section_after.start()
    
    if content_start is None:
        print(f"  WARNING: Could not find content start in {html_path}")
        return ""
    
    # Content ends at <footer
    footer_match = re.search(r'<footer\b', content[content_start:])
    if footer_match:
        content_end = content_start + footer_match.start()
    else:
        content_end = len(content)
    
    # Also look for page-specific scripts before footer
    script_match = re.search(r'<script(?![^>]*mobile-menu])[^<]*>.*?</script>', content[content_start:], re.DOTALL)
    
    page_content = content[content_start:content_end].strip()
    
    # Also extract any page-specific <script> blocks that come after content but before </body>
    # (like the index.html blog fetcher, calculator logic, etc.)
    after_content = content[content_end:]
    footer_end_match = re.search(r'</footer>', after_content)
    if footer_end_match:
        after_footer = after_content[footer_end_match.end():]
        # Extract any <script> blocks that aren't the mobile menu script
        extra_scripts = re.findall(r'<script[^>]*>.*?</script>', after_footer, re.DOTALL)
        mobile_menu_scripts = [s for s in extra_scripts if 'mobile-menu' in s or 'm-panel' in s]
        page_scripts = [s for s in extra_scripts if s not in mobile_menu_scripts]
        # Also extract any extra HTML (like the mobile bottom bar on index.html)
        extra_html = re.sub(r'<script[^>]*>.*?</script>', '', after_footer, flags=re.DOTALL).strip()
        extra_html = re.sub(r'</body>\s*</html>\s*', '', extra_html).strip()
        if extra_html:
            page_content += "\n" + extra_html
        for s in page_scripts:
            page_content += "\n" + s
    
    return page_content


def extract_head_extras(html_path, page_meta=None):
    """Extract page-specific head content. Use pages.yml if available, fallback to HTML parsing."""
    fname = os.path.basename(html_path).replace('.html', '')
    
    # If we have metadata from pages.yml, use it
    if page_meta:
        title = page_meta.get('title', f'{fname} | 派币中文网')
        desc = page_meta.get('description', '')
        body_extra = ''
        if page_meta.get('body_class') == '':
            body_extra = ''  # no pt-24
        else:
            body_extra = ' pt-24'
        
        canonical = f'https://pibizh.com/{fname}.html'
        head_extra = f'''    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="/static/favicon.png">
    <meta property="og:locale" content="zh_CN">'''
        return head_extra, body_extra
    
    # Fallback: extract from HTML file
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    head_start = content.find("</style>")
    if head_start == -1:
        return "", ""
    
    head_end = content.find('<link rel="stylesheet" href="https://fonts.loli.net', head_start)
    if head_end == -1:
        head_end = content.find("</head>", head_start)
    
    head_extra = content[head_start + len("</style>"):head_end].strip()
    
    body_match = re.search(r'<body class="([^"]*)"', content)
    body_class = body_match.group(1) if body_match else "hero-bg min-h-screen pt-24"
    
    base_classes = {"hero-bg", "min-h-screen", "pt-24"}
    extra_classes = [c for c in body_class.split() if c not in base_classes]
    body_extra = (" " + " ".join(extra_classes)) if extra_classes else ""
    if "pt-24" not in body_class:
        body_extra = ""
    
    return head_extra, body_extra


def build_page(page_file, source_html, page_meta=None):
    """Build a single page from source HTML using templates."""
    head_extra, body_extra = extract_head_extras(source_html, page_meta)
    page_content = extract_page_content(source_html)
    
    # Assemble the page
    head_html = HEAD_TMPL.replace("{{HEAD_EXTRA}}", head_extra).replace("{{BODY_CLASS}}", body_extra)
    
    full_html = head_html + "\n" + NAV_TMPL + "\n    " + page_content + "\n" + FOOTER_TMPL
    
    # Clean up any duplicate </body></html>
    full_html = re.sub(r'(</body>\s*</html>\s*)+', '</body>\n</html>', full_html)
    
    return full_html


def main():
    # Load page metadata from pages.yml
    pages_yml_path = PAGES_DIR / "pages.yml"
    page_metas = {}
    if pages_yml_path.exists():
        with open(pages_yml_path, "r", encoding="utf-8") as f:
            page_metas = yaml.safe_load(f) or {}
        print(f"Loaded {len(page_metas)} page metas from pages.yml")
    
    # Find all HTML files in root that should be rebuilt
    # Skip: 404.html (special), blog/ (separate handling)
    html_files = sorted(BASE_DIR.glob("*.html"))
    
    # Files that have the standard page structure (header + content + footer)
    # We detect this by checking if they have <!-- 导航栏 or <header
    rebuild_count = 0
    skip_count = 0
    
    for html_path in html_files:
        name = html_path.name
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Only rebuild pages that have our standard navigation structure
        if "<!-- 导航栏" not in content and '<header class="fixed' not in content:
            print(f"SKIP: {name} (no standard nav)")
            skip_count += 1
            continue
        
        # Check if this page has a <head> section with our templates
        if "<!DOCTYPE" not in content:
            print(f"SKIP: {name} (no DOCTYPE - already broken, needs manual fix)")
            skip_count += 1
            continue
        
        print(f"BUILD: {name}")
        
        # Back up original
        backup_dir = BASE_DIR / "_backups"
        backup_dir.mkdir(exist_ok=True)
        if not (backup_dir / name).exists():
            import shutil
            shutil.copy2(html_path, backup_dir / name)
        
        # Build the page
        # Get page metadata
        page_key = name.replace('.html', '')
        meta = page_metas.get(page_key)
        
        built_html = build_page(name, str(html_path), meta)
        
        # Write output
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(built_html)
        
        rebuild_count += 1
    
    print(f"\nDone! Rebuilt {rebuild_count} pages, skipped {skip_count}")


if __name__ == "__main__":
    main()
