#!/usr/bin/env python3
"""
精准修复各页面配色和结构问题：

问题汇总：
1. mining-tutorial.html + wallet-guide.html:
   - body class="hero-bg ..." → body 是深色紫色渐变背景，但 section 内文字 text-white 与浅色内容 section 冲突
   - body 不应该是 hero-bg，应该是白色背景
   - "text-white" 在浅色 section 里变成白字白底 → 看不见
   - <main> 有重复 flex-1 + 缺少 <section> opening（</section> 孤儿标签）
   - 内联 <style> 有破损的 .dropdown:hover { (没有闭合)

2. technical-whitepaper.html:
   - site-footer 在 </main> 内部，应该在外面

3. roadmap.html:
   - site-footer 在 </main> 后面但顺序对了，检查一下

4. 全站所有页面:
   - 修复 text-white 在浅色 bg section 里的问题
   - 统一 step-card / section-card 文字颜色

修复策略：
- mining-tutorial.html 和 wallet-guide.html：
  * 去掉 body 的 hero-bg
  * 修复破损的 style 块
  * 修复 <main> 的重复 flex-1
  * 修复孤儿 </section>
  * 浅色 section (bg-white, bg-[#f5f0ff]) 里的 text-white → text-[#1a1a2e]
  * 浅色 bg 里的 strong.text-white → strong.text-[#1a1a2e]

- technical-whitepaper.html:
  * 把 site-footer 移到 </main> 外面

- 全站：
  * 修复 style 块里的破损规则
  * step-card / section-card 内部 text-white 换成 text-[#1a1a2e]（卡片背景是白色）
"""
import re, os

DIR = '/home/andy/.openclaw/workspace/git_deploy/blowfish-pi'

def fix_mining_tutorial():
    path = os.path.join(DIR, 'mining-tutorial.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. Remove hero-bg from body (body should be white)
    html = html.replace('<body class="hero-bg min-h-screen flex flex-col">', '<body class="min-h-screen flex flex-col">')
    html = html.replace('<body class="hero-bg min-h-screen">', '<body class="min-h-screen flex flex-col">')
    
    # 2. Fix broken style block (.dropdown:hover with no closing brace)
    html = re.sub(r'\.dropdown:hover\s*\n\s*\n', '', html)
    # Remove leftover closing brace from broken style
    html = re.sub(r'(\s*\}\s*\n\s*\.step-card)', '\n        .step-card', html)
    
    # 3. Fix double flex-1
    html = html.replace('<main class="flex-1 flex-1">', '<main class="flex-1">')
    
    # 4. Fix orphan </section> at top of main
    html = html.replace('<div id="site-nav"></div><main class="flex-1">\n\n    \n    </section>', 
                        '<div id="site-nav"></div><main class="flex-1">')
    # Also handle alternate whitespace
    html = re.sub(r'(<div id="site-nav"></div><main class="flex-1">)\s*</section>', r'\1', html)
    
    # 5. Fix text-white in light sections
    # Section bg-[#f5f0ff] and bg-white: text in table should be dark, not white
    # Replace text-white in table rows that are inside light sections
    # Strategy: fix all text-white inside <section class="... bg-[#f5f0ff] ..."> and <section class="... bg-white ...">
    
    # Fix table text (compare table - text-white on white/light bg)
    # The compare table has th with text-white on light section
    html = html.replace(
        '<th class="text-left py-4 px-6 text-[#f4af47] font-black text-sm uppercase tracking-widest">对比维度</th><th class="text-center py-4 px-6 text-white font-black text-sm uppercase tracking-widest">Pi Network</th><th class="text-center py-4 px-6 text-white font-black text-sm uppercase tracking-widest">比特币 (BTC)</th>',
        '<th class="text-left py-4 px-6 text-[#f4af47] font-black text-sm uppercase tracking-widest">对比维度</th><th class="text-center py-4 px-6 text-[#1a1a2e] font-black text-sm uppercase tracking-widest">Pi Network</th><th class="text-center py-4 px-6 text-[#1a1a2e] font-black text-sm uppercase tracking-widest">比特币 (BTC)</th>'
    )
    
    # Fix table body cells text-white (in light bg section)
    html = re.sub(r'<td class="py-4 px-6 text-white font-medium">', '<td class="py-4 px-6 text-[#374151] font-medium">', html)
    html = re.sub(r'<td class="py-4 px-6 text-center text-white font-bold">', '<td class="py-4 px-6 text-center text-[#1a1a2e] font-bold">', html)
    html = re.sub(r'<td class="py-4 px-6 text-center text-white font-medium">', '<td class="py-4 px-6 text-center text-[#374151] font-medium">', html)
    
    # Fix paragraph text-white in light section
    html = html.replace(
        '<p class="text-white text-lg leading-relaxed mb-10 max-w-3xl">Pi Network 采用<strong class="text-white">',
        '<p class="text-[#374151] text-lg leading-relaxed mb-10 max-w-3xl">Pi Network 采用<strong class="text-[#1a1a2e]">'
    )
    
    # Fix feature boxes (不耗电/不费流量/不伤手机) in light section
    html = html.replace('<h3 class="text-white font-black text-lg mb-2">不耗电</h3><p class="text-white text-sm">', 
                        '<h3 class="text-[#1a1a2e] font-black text-lg mb-2">不耗电</h3><p class="text-[#374151] text-sm">')
    html = html.replace('<h3 class="text-white font-black text-lg mb-2">不费流量</h3><p class="text-white text-sm">', 
                        '<h3 class="text-[#1a1a2e] font-black text-lg mb-2">不费流量</h3><p class="text-[#374151] text-sm">')
    html = html.replace('<h3 class="text-white font-black text-lg mb-2">不伤手机</h3><p class="text-white text-sm">', 
                        '<h3 class="text-[#1a1a2e] font-black text-lg mb-2">不伤手机</h3><p class="text-[#374151] text-sm">')
    
    # Fix "运行节点加成" card (white text in light section)
    html = html.replace('<h3 class="text-white font-black text-xl mb-3">运行节点加成</h3>',
                        '<h3 class="text-[#1a1a2e] font-black text-xl mb-3">运行节点加成</h3>')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Fixed mining-tutorial.html")

def fix_wallet_guide():
    path = os.path.join(DIR, 'wallet-guide.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. Remove hero-bg from body
    html = html.replace('<body class="hero-bg min-h-screen flex flex-col">', '<body class="min-h-screen flex flex-col">')
    html = html.replace('<body class="hero-bg min-h-screen">', '<body class="min-h-screen flex flex-col">')
    
    # 2. Fix double flex-1
    html = html.replace('<main class="flex-1 flex-1">', '<main class="flex-1">')
    
    # 3. Fix text-white in light sections (bg-white section - wallet section)
    # Step cards in wallet section have text-white on white bg
    html = html.replace('<h4 class="text-lg font-black mb-3 text-white mt-2">打开 Pi Browser</h4><p class="text-white text-sm">下载并打开 Pi Browser 应用，使用你的 Pi 账号登录</p>',
                        '<h4 class="text-lg font-black mb-3 text-[#1a1a2e] mt-2">打开 Pi Browser</h4><p class="text-[#374151] text-sm">下载并打开 Pi Browser 应用，使用你的 Pi 账号登录</p>')
    html = html.replace('<h4 class="text-lg font-black mb-3 text-white mt-2">创建钱包</h4><p class="text-white text-sm">在 Pi Browser 首页点击「Pi Wallet」，按提示创建你的钱包</p>',
                        '<h4 class="text-lg font-black mb-3 text-[#1a1a2e] mt-2">创建钱包</h4><p class="text-[#374151] text-sm">在 Pi Browser 首页点击「Pi Wallet」，按提示创建你的钱包</p>')
    
    # Fix all remaining text-white in step-card (they have bg-[#f8f9fa] background)
    # Use regex for any remaining ones
    html = re.sub(r'(<div class="step-card[^"]*">[^<]*<div[^>]*>\d+</div><h4 class="[^"]*?)text-white([^"]*")',
                  r'\1text-[#1a1a2e]\2', html)
    html = re.sub(r'(class="[^"]*step-card[^"]*".*?<p class=")text-white( text-sm")',
                  r'\1text-[#374151]\2', html, flags=re.DOTALL)
    
    # Fix broken style block if any
    html = re.sub(r'\.dropdown:hover\s*\n\s*\n', '', html)
    html = re.sub(r'(\s*\}\s*\n\s*\.step-card)', '\n        .step-card', html)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Fixed wallet-guide.html")

def fix_technical_whitepaper():
    path = os.path.join(DIR, 'technical-whitepaper.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # site-footer is inside </main> - move it outside
    # Pattern: <div id="site-footer"></div>\n        </main>
    html = html.replace('<div id="site-footer"></div>\n        </main>', '</main>\n<div id="site-footer"></div>')
    html = html.replace('<div id="site-footer"></div>\n    </main>', '</main>\n<div id="site-footer"></div>')
    # Also handle </main><div id="site-footer">
    html = re.sub(r'(<div id="site-footer"></div>)(\s*</main>)', r'</main>\n\1', html)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Fixed technical-whitepaper.html")

def fix_roadmap():
    path = os.path.join(DIR, 'roadmap.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Check structure: </main><div id="site-footer"> is correct
    # Fix double flex-1 if present
    html = html.replace('<main class="flex-1 flex-1">', '<main class="flex-1">')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Fixed roadmap.html")

def fix_all_pages_global():
    """Fix remaining global issues across all pages"""
    for fname in sorted(os.listdir(DIR)):
        if not fname.endswith('.html'):
            continue
        path = os.path.join(DIR, fname)
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        original = html
        
        # Fix double flex-1 everywhere
        html = html.replace('class="flex-1 flex-1"', 'class="flex-1"')
        
        # Fix broken .dropdown:hover style remnant
        html = re.sub(r'\s*\.dropdown:hover\s*\n\s*\n\s*\}', '', html)
        
        # Fix site-footer inside </main> pattern (technical-whitepaper style)
        html = re.sub(
            r'<div id="site-footer"></div>(\s*)</main>',
            r'\1</main>\n<div id="site-footer"></div>',
            html
        )
        
        # Fix body missing flex flex-col
        html = re.sub(r'<body class="min-h-screen">', '<body class="min-h-screen flex flex-col">', html)
        
        if html != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ Global fix applied: {fname}")

# Run all fixes
fix_mining_tutorial()
fix_wallet_guide()
fix_technical_whitepaper()
fix_roadmap()
fix_all_pages_global()
print("\nAll fixes done!")
