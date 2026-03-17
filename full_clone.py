import requests
from bs4 import BeautifulSoup
import os

# 目标：全量、1:1 复刻 Pi 白皮书，绝不省略任何细节
URL = "https://minepi.com/white-paper/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def clone_whitepaper():
    print("[*] 正在执行全量抓取: " + URL)
    r = requests.get(URL, headers=HEADERS)
    if r.status_code != 200:
        print("[!] 抓取失败")
        return

    soup = BeautifulSoup(r.text, 'html.parser')
    # 锁定官网正文容器 (Salient 框架常用的容器)
    content_area = soup.find('div', class_='post-content') or soup.find('main')
    
    if not content_area:
        print("[!] 未能锁定正文容器")
        return

    # 提取全量 HTML 内容 (包含所有段落、标题、列表)
    full_html = content_area.encode_contents().decode('utf-8')
    
    # 构造完整的中文包装页面
    web_page = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>技术白皮书 (1:1 全量官方版) | Pi Network 中文网</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #0f021a; color: white; line-height: 2; padding: 50px 20px; }}
            .official-content h1 {{ font-size: 4rem; font-weight: 900; color: #f4af47; margin-bottom: 2rem; }}
            .official-content h2 {{ font-size: 2.5rem; font-weight: 800; margin: 4rem 0 1.5rem; }}
            .official-content p {{ margin-bottom: 1.5rem; color: #cbd5e1; font-size: 1.1rem; }}
            .official-content ul {{ list-style: disc; margin-left: 2rem; }}
        </style>
    </head>
    <body>
        <nav class="p-6 border-b border-white/5"><a href="/index.html">← 返回首页</a></nav>
        <div class="max-w-4xl mx-auto official-content">
            {full_html}
        </div>
    </body>
    </html>
    """
    
    with open('whitepaper.html', 'w', encoding='utf-8') as f:
        f.write(web_page)
    print(f"[*] 成功生成全量物理文件，字数：{len(full_html)}")

if __name__ == "__main__":
    clone_whitepaper()
