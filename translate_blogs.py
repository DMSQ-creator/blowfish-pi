#!/usr/bin/env python3
"""
Translate blog content and generate final HTML pages.
Uses deep-translator for batch translation with HTML tag preservation.
"""
import re, os, json, time
from deep_translator import GoogleTranslator

CACHEDIR = '/home/andy/.openclaw/workspace/git_deploy/blowfish-pi/content_cache'
OUTDIR = '/home/andy/.openclaw/workspace/git_deploy/blowfish-pi/blog'
TRANSLATION_CACHE = '/home/andy/.openclaw/workspace/git_deploy/blowfish-pi/translation_cache.json'

# Load translation cache
if os.path.exists(TRANSLATION_CACHE):
    with open(TRANSLATION_CACHE, 'r') as f:
        trans_cache = json.load(f)
else:
    trans_cache = {}

def save_cache():
    with open(TRANSLATION_CACHE, 'w') as f:
        json.dump(trans_cache, f, ensure_ascii=False, indent=2)

def translate_text(text):
    """Translate English text to Chinese, with caching."""
    if not text or not text.strip():
        return text
    key = text.strip()
    if key in trans_cache:
        return trans_cache[key]
    
    # Skip very short text or numbers
    if len(key) < 3 or key.replace(' ','').replace('.','').replace(',','').isdigit():
        return text
    
    try:
        result = GoogleTranslator(source='en', target='zh-CN').translate(key)
        if result:
            trans_cache[key] = result
            return result
    except Exception as e:
        print(f"  Translation error: {e}")
        time.sleep(2)
        try:
            result = GoogleTranslator(source='en', target='zh-CN').translate(key)
            if result:
                trans_cache[key] = result
                return result
        except:
            pass
    
    return text

def translate_html_content(html):
    """Translate text content within HTML while preserving tags."""
    # Split HTML into tags and text
    parts = re.split(r'(<[^>]+>)', html)
    translated_parts = []
    
    text_buffer = []
    for part in parts:
        if part.startswith('<'):
            # Flush text buffer
            if text_buffer:
                combined = ''.join(text_buffer)
                if combined.strip() and len(combined.strip()) > 2:
                    translated = translate_text(combined.strip())
                    translated_parts.append(translated)
                else:
                    translated_parts.append(combined)
                text_buffer = []
            translated_parts.append(part)
        else:
            text_buffer.append(part)
    
    # Flush remaining text
    if text_buffer:
        combined = ''.join(text_buffer)
        if combined.strip() and len(combined.strip()) > 2:
            translated = translate_text(combined.strip())
            translated_parts.append(translated)
        else:
            translated_parts.append(combined)
    
    return ''.join(translated_parts)

def translate_paragraphs(html):
    """Translate content paragraph by paragraph for better quality."""
    # Split into top-level block elements
    blocks = re.split(r'(<(?:p|h[1-6]|blockquote|li|figcaption|td|th)\b[^>]*>|</(?:p|h[1-6]|blockquote|li|figcaption|td|th)>)', html)
    
    result = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        # Check if this is an opening tag
        open_match = re.match(r'^<(p|h[1-6]|blockquote|li|figcaption|td|th)\b[^>]*>$', block)
        if open_match:
            result.append(block)  # Keep opening tag
            i += 1
            # Collect content until closing tag
            tag = open_match.group(1)
            close_tag = f'</{tag}>'
            content_parts = []
            while i < len(blocks) and blocks[i] != close_tag:
                content_parts.append(blocks[i])
                i += 1
            if i < len(blocks):
                # Translate the content between tags
                content = ''.join(content_parts)
                inner_text = re.sub(r'<[^>]+>', '', content).strip()
                if inner_text and len(inner_text) > 3:
                    # Translate the text nodes within the content
                    translated_content = translate_html_content(content)
                    result.append(translated_content)
                else:
                    result.extend(content_parts)
                result.append(close_tag)
                i += 1
            else:
                result.extend(content_parts)
        else:
            # Check for img, iframe, br, hr - keep as-is
            if re.match(r'^<(?:img|iframe|br|hr)\b', block):
                result.append(block)
            elif not block.strip() or re.match(r'^<[^>]+>$', block):
                result.append(block)
            else:
                # Plain text outside tags - translate
                text = block.strip()
                if text and len(text) > 3:
                    translated = translate_text(text)
                    result.append(translated)
                else:
                    result.append(block)
            i += 1
    
    return ''.join(result)

# Blog metadata
BLOG_META = {
    'pi-day-2025': ('Pi Day 2025：全层级生态实用性拓展', '2025-03-14', '官方公告'),
    '100-days-open-network': ('开放网络 100 天：实用性驱动的生态系统', '2025-06-19', '官方公告'),
    'open-network': ('Pi 开放网络正式上线！', '2025-02-19', '官方公告'),
    'open-network-launch-date': ('Pi 开放网络定于 2025 年 2 月 20 日上线！', '2025-02-11', '官方公告'),
    'open-network-update': ('开放网络条件与时间线更新！', '2024-12-19', '官方公告'),
    'pi-lockup': ('锁仓提醒：先锋可选择锁定 Pi 以促进生态系统', '2025-08-01', '官方公告'),
    'pi2day2025': ('Pi2Day 2025：推出 AI 倡议以扩展下一代应用', '2025-06-27', '官方公告'),
    'pi2day2025-challenge': ('Pi2Day 2025 生态系统挑战赛', '2025-06-27', '官方公告'),
    'pi2day-2025-recap': ('Pi2Day 2025 回顾', '2025-07-17', '官方公告'),
    'pi-hackathon-2025': ('Pi 黑客松 2025：在开放网络时代增强 Pi 实用性', '2025-08-15', '官方公告'),
    'pi-hackathon-2025-begins': ('Pi 黑客松 2025 正式开始！', '2025-08-21', '官方公告'),
    'dex-amm-token-creation': ('Pi DEX、AMM 流动性池和代币创建功能现已上线', '2025-09-30', '官方公告'),
    'pi-linux-node': ('Linux 节点发布与即将到来的协议升级', '2025-08-27', '官方公告'),
    'kyc-ai-integration': ('AI 升级 Pi KYC 加速验证处理，为先锋解锁', '2025-12-05', '官方公告'),
    'hackathon-2025-winners': ('Pi 黑客松 2025 获奖者公布', '2025-12-11', '官方公告'),
    '10-minutes-pi-payments': ('10 分钟内集成 Pi 支付：新功能让开发更便捷', '2026-01-09', '官方公告'),
    'app-studio-code': ('Pi App Studio 更新：代码下载/上传功能与用户测试', '2025-11-14', '官方公告'),
    'pi-cidi-games': ('Pi Network 与赤迪游戏合作加速 Web3 游戏发展', '2025-11-26', '官方公告'),
    'pi-app-studio-updates': ('Pi App Studio 更新：扩展自定义与生态集成', '2025-10-16', '官方公告'),
    'pi-node-0-5-4': ('Pi 节点 0.5.4 版本更新', '2025-11-06', '官方公告'),
    'wallet-activation': ('通过新的钱包激活方式拓展 Pi 主网生态系统访问', '2025-05-02', '官方公告'),
    'pi-wallet-safety': ('保护你的 Pi 钱包：重要安全提醒', '2025-06-05', '官方公告'),
    'fast-track-kyc': ('快速通道 KYC 助力生态应用更早激活钱包', '2025-09-18', '官方公告'),
}

FOOTER = '''    <!-- 统一 Footer -->
    <footer class="py-10 bg-[#1e0a27] text-center border-t border-white/5">
        <img alt="Pi Network Logo" src="/static/favicon.png" class="w-8 h-8 mb-4 mx-auto grayscale brightness-200">
        <p class="text-sm font-bold text-gray-500 mb-4">© 2026 PI NETWORK 官方中文社区 · 邀请码: nbjh</p>
        <div class="flex flex-wrap justify-center gap-6 text-sm font-bold text-gray-600">
            <a href="../index.html" class="hover:text-white">首页</a>
            <a href="../blog.html" class="hover:text-white">资讯中心</a>
            <a href="../reg.html" class="hover:text-[#f4af47]">下载注册</a>
            <a href="../faq.html" class="hover:text-white">常见问题</a>
        </div>
    </footer>'''

# Process each blog post
slugs = list(BLOG_META.keys())
for idx, slug in enumerate(slugs):
    cn_title, date, category = BLOG_META[slug]
    raw_path = os.path.join(CACHEDIR, f'{slug}_raw.html')
    
    if not os.path.exists(raw_path):
        print(f"SKIP: {slug} - no raw content")
        continue
    
    with open(raw_path, 'r', errors='ignore') as f:
        content_html = f.read()
    
    print(f"[{idx+1}/{len(slugs)}] Translating {slug} ({len(content_html)} chars)...")
    
    # Translate content
    translated_content = translate_paragraphs(content_html)
    
    # Clean up images
    translated_content = re.sub(r'<img\s+([^>]*)>', lambda m: f'<img {m.group(1)} class="w-full rounded-3xl" loading="lazy">', translated_content)
    
    # Clean up iframes
    translated_content = re.sub(r'<iframe\s+([^>]*)></iframe>', 
                         lambda m: f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:1.5rem;margin:2rem 0;"><iframe {m.group(1)} style="position:absolute;top:0;left:0;width:100%;height:100%;" frameborder="0" allowfullscreen></iframe></div>', 
                         translated_content)
    
    # Remove any remaining script tags
    translated_content = re.sub(r'<script[^>]*>.*?</script>', '', translated_content, flags=re.DOTALL)
    
    # Generate HTML page
    page_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/png" href="/static/favicon.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cn_title} | Pi Network 中文网</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #0f021a; color: white; line-height: 1.8; font-family: sans-serif; }}
        .text-pi-gold {{ background: linear-gradient(90deg, #f4af47 0%, #fab44b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .prose p {{ margin-bottom: 1.8rem; font-size: 1.15rem; color: #cbd5e1; text-align: justify; }}
        .prose h2 {{ font-size: 2.2rem; font-weight: 900; margin: 4rem 0 2rem; color: #f4af47; }}
        .prose h3 {{ font-size: 1.6rem; font-weight: 700; margin: 3rem 0 1.5rem; color: #e2e8f0; }}
        .prose h4 {{ font-size: 1.3rem; font-weight: 700; margin: 2rem 0 1rem; color: #e2e8f0; }}
        .prose blockquote {{ border-left: 4px solid #f4af47; padding-left: 1.5rem; margin: 2rem 0; font-style: italic; color: #f4af47; font-weight: bold; }}
        .prose img {{ border-radius: 1.5rem; margin: 2rem 0; }}
        .prose ul {{ list-style: disc; padding-left: 2rem; margin-bottom: 1.5rem; }}
        .prose ol {{ list-style: decimal; padding-left: 2rem; margin-bottom: 1.5rem; }}
        .prose li {{ margin-bottom: 0.5rem; color: #cbd5e1; font-size: 1.1rem; }}
        .prose a {{ color: #f4af47; text-decoration: underline; }}
        .prose strong {{ color: #f4af47; font-weight: bold; }}
        .prose em {{ color: #cbd5e1; }}
        .prose table {{ width: 100%; border-collapse: collapse; margin: 2rem 0; }}
        .prose th, .prose td {{ border: 1px solid rgba(255,255,255,0.1); padding: 0.75rem 1rem; color: #cbd5e1; }}
        .prose th {{ background: rgba(244,175,71,0.1); color: #f4af47; font-weight: bold; }}
    </style>
</head>
<body class="min-h-screen">
    <nav class="p-6 border-b border-white/5 bg-[#1e0a27]/80 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <a href="../blog.html" class="text-gray-400 hover:text-white font-bold">← 返回社区资讯</a>
            <span class="text-[#f4af47] font-black uppercase">{category}</span>
        </div>
    </nav>
    <main class="max-w-3xl mx-auto py-20 px-6">
        <h1 class="text-4xl md:text-6xl font-black mb-4 tracking-tighter leading-tight">{cn_title}</h1>
        <p class="text-gray-500 mb-10">{date}</p>
        <div class="prose max-w-none">
{translated_content}
        </div>
    </main>
{FOOTER}
</body>
</html>'''
    
    out_path = os.path.join(OUTDIR, f'{slug}.html')
    with open(out_path, 'w') as f:
        f.write(page_html)
    
    print(f"  -> Saved {out_path} ({len(page_html)} bytes)")
    
    # Save cache every 3 posts
    if (idx + 1) % 3 == 0:
        save_cache()
        print(f"  [Cache saved: {len(trans_cache)} entries]")

# Final cache save
save_cache()
print(f"\nAll {len(slugs)} blog pages translated and generated!")
print(f"Translation cache: {len(trans_cache)} entries")
