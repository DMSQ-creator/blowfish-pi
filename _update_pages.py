#!/usr/bin/env python3
"""
Batch update all HTML pages on pibizh.com:
1. Add site.css link (before </head>)
2. Add inject-components.js (before </body>)
3. Replace old nav/header with <div id="site-nav"></div>
4. Replace old footer with <div id="site-footer"></div>
5. Remove duplicated inline styles that are now in site.css
6. Ensure body has correct classes
7. Remove old fixed-cta if present (now in inject-components.js)
"""
import re, os, sys

DIR = '/home/andy/.openclaw/workspace/git_deploy/blowfish-pi'

# Pages that have the full navbar (Style A) - need to replace <header>...</header> + mobile menu
# Pages that have the simple nav (Style B) - need to replace <nav>...</nav>

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    filename = os.path.basename(filepath)
    print(f"Processing {filename}...")
    
    original = html
    
    # 1. Add site.css if not already present
    if 'site.css' not in html:
        html = html.replace('</head>', '<link rel="stylesheet" href="site.css">\n</head>')
    
    # 2. Add inject-components.js if not already present (before </body>)
    if 'inject-components.js' not in html:
        html = html.replace('</body>', '<script src="inject-components.js"></script>\n</body>')
    
    # 3. Remove old fixed-cta (various forms)
    html = re.sub(
        r'<a\s+href=["\']reg\.html["\']\s+class=["\']fixed-cta[^>]*>.*?</a>',
        '', html, flags=re.DOTALL
    )
    
    # 4. Replace Style A navbar (<header class="fixed w-full z-[100] nav-blur ...">...</header>)
    # Also remove the mobile menu div that follows
    style_a_header = re.search(
        r'<header\s+class=["\']fixed\s+w-full\s+z-\[100\]\s+nav-blur[^>]*>.*?</header>',
        html, re.DOTALL
    )
    if style_a_header:
        html = html[:style_a_header.start()] + '<div id="site-nav"></div>' + html[style_a_header.end():]
        # Also remove the mobile menu div
        mobile_menu = re.search(
            r'<div\s+id=["\']mobile-menu["\'][^>]*>.*?</div>\s*</div>',
            html, re.DOTALL
        )
        if mobile_menu:
            html = html[:mobile_menu.start()] + html[mobile_menu.end():]
    
    # 5. Replace Style B navbar (simple <nav class="p-6 border-b ...bg-[#593B8B]...">...</nav>)
    style_b_nav = re.search(
        r'<nav\s+class=["\']p-6\s+border-b[^>]*bg-\[#593B8B\][^>]*>.*?</nav>',
        html, re.DOTALL
    )
    if style_b_nav and 'site-nav' not in html:
        html = html[:style_b_nav.start()] + '<div id="site-nav"></div>' + html[style_b_nav.end():]
    
    # 6. Replace old footer(s) - various forms
    # Pattern: <footer ...>...</footer>
    footer_patterns = [
        r'<footer\s+class=["\']py-10\s+bg-\[#252525\][^>]*>.*?</footer>',
        r'<footer\s+class=["\']py-12\s+bg-\[#252525\][^>]*>.*?</footer>',
    ]
    for pat in footer_patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            html = html[:m.start()] + '<div id="site-footer"></div>' + html[m.end():]
            break
    
    # 7. Clean up: remove old inline <style> blocks that duplicate site.css
    # Remove .nav-blur, .dropdown-menu, .text-pi-gold, #mobile-menu, .fixed-cta, .hero-bg, .blog-card rules
    # But keep page-specific styles!
    # We'll remove the common properties from inline <style>
    
    # Remove body{...} inline style that's now in site.css
    html = re.sub(r'body\s*\{[^}]*background-color[^}]*\}', '', html)
    
    # Remove .text-pi-gold inline (now in site.css)
    html = re.sub(r'\.text-pi-gold\s*\{[^}]*\}', '', html)
    
    # Remove .dropdown-menu inline
    html = re.sub(r'\.dropdown-menu\s*\{[^}]*\}', '', html)
    html = re.sub(r'\.dropdown-menu\s+a\s*\{[^}]*\}', '', html)
    html = re.sub(r'\.dropdown-menu\s+a:last-child\s*\{[^}]*\}', '', html)
    html = re.sub(r'\.dropdown-menu\s+a:hover\s*\{[^}]*\}', '', html)
    
    # Remove .nav-blur inline
    html = re.sub(r'\.nav-blur\s*\{[^}]*\}', '', html)
    
    # Remove #mobile-menu inline
    html = re.sub(r'#mobile-menu\s*\{[^}]*\}', '', html)
    html = re.sub(r'#mobile-menu\.open\s*\{[^}]*\}', '', html)
    
    # Remove .fixed-cta + @keyframes bounce
    html = re.sub(r'\.fixed-cta\s*\{[^}]*\}', '', html)
    html = re.sub(r'@keyframes\s+bounce\s*\{[^}]*\}[^}]*\}', '', html)
    
    # Remove .hero-bg inline
    html = re.sub(r'\.hero-bg\s*\{[^}]*\}', '', html)
    
    # Remove .blog-card inline (now in site.css)
    html = re.sub(r'\.blog-card\s*\{[^}]*\}', '', html)
    html = re.sub(r'\.blog-card:hover\s*\{[^}]*\}', '', html)
    
    # Remove .dropdown:hover inline
    html = re.sub(r'\.dropdown:hover\s+\.dropdown-menu\s*\{[^}]*\}', '', html)
    
    # 8. Ensure body has min-h-screen and flex flex-col for sticky footer
    if '<body' in html:
        body_tag = re.search(r'<body[^>]*>', html)
        if body_tag:
            old_tag = body_tag.group()
            if 'min-h-screen' not in old_tag:
                new_tag = old_tag.replace('<body', '<body class="min-h-screen flex flex-col"')
                # Remove old class if it had one
                new_tag = re.sub(r'class="([^"]*)"', lambda m: f'class="min-h-screen flex flex-col {m.group(1)}"', old_tag) if 'class=' in old_tag else new_tag
                html = html.replace(old_tag, new_tag, 1)
    
    # 9. Wrap main content in <main class="flex-1"> if not already
    if '<main' not in html:
        # Find content between nav and footer placeholders
        nav_pos = html.find('<div id="site-nav"></div>')
        footer_pos = html.find('<div id="site-footer"></div>')
        if nav_pos != -1 and footer_pos != -1:
            nav_end = nav_pos + len('<div id="site-nav"></div>')
            main_content = html[nav_end:footer_pos]
            html = html[:nav_end] + '<main class="flex-1">' + main_content + '</main>' + html[footer_pos:]
    
    # 10. Remove duplicate <p>邀请码 in mobile menu remnants
    html = re.sub(r'<p[^>]*class=["\'][^"\']*text-center[^"\']*text-white[^"\']*text-xs[^"\']*uppercase[^"\']*tracking-widest[^"\']*font-bold[^"\']*mt-auto[^"\']*["\'][^>]*>推荐邀请码:\s*nbjh</p>', '', html)
    html = re.sub(r'<p[^>]*class=["\'][^"\']*text-center[^"\']*text-white[^"\']*text-xs[^"\']*uppercase[^"\']*tracking-widest[^"\']*font-bold["\'][^>]*>推荐邀请码:\s*nbjh</p>', '', html)
    
    # Clean up empty lines
    html = re.sub(r'\n{4,}', '\n\n\n', html)
    
    if html != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✅ Updated {filename}")
    else:
        print(f"  ⏭️ No changes needed for {filename}")

# Process all HTML files
for fname in sorted(os.listdir(DIR)):
    if fname.endswith('.html'):
        process_file(os.path.join(DIR, fname))

print("\nDone! All pages updated.")
