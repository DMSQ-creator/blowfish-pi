import os
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

# ==========================================
# Pi Network 1:1 全量内容同步引擎
# ==========================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://minepi.com/'
}

def sync_page(url, target_file, title_cn):
    print(f"[*] 正在抓取官网原文: {url}")
    try:
        # 使用 impersonate 绕过 NitroPack 防护
        r = requests.get(url, headers=HEADERS, impersonate="chrome120")
        if r.status_code != 200:
            print(f"[!] 抓取失败，状态码: {r.status_code}")
            return

        soup = BeautifulSoup(r.text, 'html.parser')
        # 锁定正文核心容器
        content = soup.find('div', class_='post-content') or soup.find('article')
        
        if not content:
            print("[!] 找不到正文内容，请检查选择器")
            return

        # 移除所有脚本和多余标签，保留 1:1 文本和图片
        for s in content(['script', 'style', 'nav', 'header', 'footer']):
            s.decompose()

        full_body = content.decode_contents()

        # 构造物理 HTML
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title_cn} | 派币中文网</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ background-color: #0f021a; color: white; line-height: 2; font-family: sans-serif; padding: 50px 20px; }}
                .official-content {{ max-width: 900px; margin: 0 auto; }}
                .official-content h1, .official-content h2 {{ color: #f4af47; font-weight: 900; margin-top: 3rem; }}
                .official-content p {{ margin-bottom: 1.5rem; color: #cbd5e1; font-size: 1.1rem; text-align: justify; }}
                .official-content img {{ border-radius: 20px; margin: 2rem 0; width: 100%; border: 1px solid rgba(255,255,255,0.1); }}
            </style>
        </head>
        <body>
            <nav class="p-6 border-b border-white/5 mb-10"><a href="/index.html">← 返回首页</a></nav>
            <div class="official-content">
                <h1 class="text-5xl mb-10">{title_cn}</h1>
                {full_body}
            </div>
        </body>
        </html>
        """
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"[*] 【成功】物理文件已生成: {target_file} (大小: {os.path.getsize(target_file)} 字节)")

    except Exception as e:
        print(f"[!] 错误: {e}")

if __name__ == "__main__":
    # 示例：全量同步白皮书
    sync_page("https://minepi.com/white-paper/", "technical-whitepaper.html", "技术白皮书 (官方全量版)")
