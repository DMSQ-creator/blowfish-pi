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

LLM_API_KEY = os.environ.get("LLM_API_KEY", "L5c05RSdm4mgZyr3CaC8")
LLM_API_URL = "https://api.modelverse.cn/v1/chat/completions"
LLM_MODEL = "deepseek-chat"

# 检查 token 是否配置
if not TG_BOT_TOKEN:
    print("[!] 警告：TG_BOT_TOKEN 环境变量未设置，Telegram 通知已禁用")
IMGBB_API_KEY = "0e0e8b6212d394dd3a99aac94e107c7c"  # imgbb 图床 API Key

# ==========================================
# HTML 博文模板
# ==========================================
ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="/static/favicon.png">
    <link rel="stylesheet" href="/static/tailwind.css">
    <style>
        body {{ background-color: #1e0a27; color: white; font-family: 'Inter', sans-serif; margin: 0; overflow-x: hidden; }}
        .hero-bg {{ background: linear-gradient(135deg, #1e0a27 0%, #423f88 100%); }}
        .text-pi-gold {{ background: linear-gradient(90deg, #f4af47 0%, #fab44b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .nav-blur {{ background: rgba(30, 10, 39, 0.95); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }}
        .dropdown:hover .dropdown-menu {{ display: block; }}
        .dropdown-menu {{ background: #2d1b3d; border: 1px solid rgba(255,255,255,0.2); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }}
        .dropdown-menu a {{ display: block; padding: 12px 24px; font-size: 14px; color: #ffffff !important; font-weight: 600; transition: all 0.2s; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .dropdown-menu a:last-child {{ border-bottom: none; }}
        .dropdown-menu a:hover {{ background: rgba(244,175,71,0.15); color: #f4af47 !important; }}
        #mobile-menu {{ display: none; }}
        .fixed-cta {{ position: fixed; bottom: 2rem; right: 2rem; z-index: 100; animation: bounce 2s infinite; }}
        @keyframes bounce {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
        .step-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 24px; padding: 2rem; transition: all 0.3s; }}
        .step-card:hover {{ border-color: #f4af47; background: rgba(244,175,71,0.05); }}
        .warning-box {{ background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 20px; padding: 2rem; }}
        .info-box {{ background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.3); border-radius: 20px; padding: 2rem; }}
        .section-card {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 30px; padding: 2.5rem; }}
        .breadcrumb {{ font-size: 13px; color: #999; }}
        .breadcrumb a {{ color: #f4af47; text-decoration: none; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        @media (max-width: 768px) {{ .step-card {{ padding: 1.5rem; }} .section-card {{ padding: 1.5rem; }} }}
    </style>
    
    <meta name="description" content="{title} - Pi Network 官方中文资讯，派币中文网第一时间翻译发布。">
    <link rel="canonical" href="https://pibizh.com/blog/{slug}.html">
    <meta property="og:title" content="{title} | 派币中文网">
    <meta property="og:description" content="{title} - Pi Network 官方中文资讯">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://pibizh.com/blog/{slug}.html">
    <meta property="og:locale" content="zh_CN">
    <script defer src="https://umami.cc.cd/script.js" data-website-id="40c4e4c7-3419-4e2c-aa0b-badadb809af8"></script>
    <style>
        .prose h2 {{ font-size: 2.2rem; font-weight: 900; margin: 4rem 0 2rem; color: #f4af47; border-left: 6px solid #f4af47; padding-left: 1.5rem; }}
        .prose h3 {{ font-size: 1.6rem; font-weight: 800; margin: 2.5rem 0 1.2rem; color: #fff; }}
        .prose p {{ margin-bottom: 2rem; font-size: 1.2rem; color: #cbd5e1; }}
        .prose ul {{ list-style: disc; margin-left: 2.5rem; margin-bottom: 2.5rem; }}
        .prose li {{ margin-bottom: 1rem; color: #cbd5e1; }}
        .prose blockquote {{ border-left: 4px solid #f4af47; padding-left: 1.5rem; margin: 2rem 0; font-style: italic; color: #f4af47; font-weight: bold; }}
        .img-wrap {{ margin: 4rem 0; border-radius: 40px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }}
        .prose img {{ border-radius: 1.5rem; margin: 2rem 0; }}
    </style>
<link rel="stylesheet" href="https://fonts.loli.net/css2?family=Inter:wght@400;700;900&amp;display=swap">
</head>
<body class="hero-bg min-h-screen">

<body class="hero-bg min-h-screen">
    <a href="/reg.html" class="fixed-cta hidden lg:flex bg-[#f4af47] text-[#1e0a27] p-4 rounded-2xl font-black shadow-2xl flex items-center gap-3 border-4 border-[#1e0a27]">
        <span class="text-xl">🔥</span>
        <div class="text-[10px] font-black leading-none uppercase">注册教程</div>
    </a>
        <!-- 导航栏 (1:1 官网结构复刻) -->
    <header class="fixed top-0 w-full z-[100] nav-blur border-b border-white/5">
        <nav class="container mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3 cursor-pointer" onclick="location.href='/index.html'">
                <img alt="Pi Network Logo" src="/static/favicon.png" class="w-10 h-10" loading="lazy">
                <span class="text-xl font-black tracking-tighter uppercase whitespace-nowrap">Pi Network 中文网</span>
            </div>
            
            <!-- 桌面菜单 (全量复刻) -->
            <div class="hidden lg:flex items-center gap-8">
                <a href="/price.html" class="text-[11px] font-black tracking-widest text-[#f4af47] uppercase hover:opacity-90">派币价格</a>
                <!-- Blockchain -->
                <div class="dropdown relative group">
                    <div class="text-[11px] font-black tracking-widest text-gray-400 uppercase cursor-pointer hover:text-[#f4af47] flex items-center gap-1">Pi 区块链 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
                    <div class="dropdown-menu absolute hidden pt-4 w-48 left-0">
                        <a href="/nodes.html">Pi 节点 (Node)</a>
                        <a href="/blockchain.html">区块浏览器</a>
                        <a href="/technical-whitepaper.html">技术白皮书</a>
                        <a href="/roadmap.html">项目路线图</a>
                    </div>
                </div>
                <!-- Ecosystem -->
                <div class="dropdown relative group">
                    <div class="text-[11px] font-black tracking-widest text-gray-400 uppercase cursor-pointer hover:text-[#f4af47] flex items-center gap-1">生态系统 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
                    <div class="dropdown-menu absolute hidden pt-4 w-56 left-0">
                        <a href="/developers.html">开发者中心</a>
                        <a href="/browser.html">Pi 浏览器下载</a>
                        <a href="/pi-shopping.html">Pi 购物</a>
                    </div>
                </div>
                <a href="/about.html" class="text-[11px] font-black tracking-widest text-gray-400 uppercase hover:text-[#f4af47]">关于我们</a>
                <div class="dropdown relative group">
                    <div class="text-[11px] font-black tracking-widest text-[#f4af47] uppercase cursor-pointer flex items-center gap-1">📚 Pi百科 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
                    <div class="dropdown-menu absolute hidden pt-4 w-48 right-0">
                        <a href="/pi-guide.html">百科首页</a>
                        <a href="/pi-download.html">📲 下载安装</a>
                        <a href="/mining-tutorial.html">⛏️ 挖矿教程</a>
                        <a href="/wallet-guide.html">💳 钱包交易</a>
                        <a href="/pi-mainnet.html">🚀 主网迁移</a>
                        <a href="/kyc.html">✅ KYC认证</a>
                        <a href="/pi-legit.html">🛡️ 安全与合规</a>
                    </div>
                </div>
                <!-- Community -->
                <div class="dropdown relative group">
                    <div class="text-[11px] font-black tracking-widest text-[#f4af47] uppercase cursor-pointer flex items-center gap-1">社区资讯 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
                    <div class="dropdown-menu absolute hidden pt-4 w-52 left-0">
                        <a href="/blog.html">官方新闻动态</a>
                        <a href="/pi-news.html">Pi 最新动态</a>
                        <a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer">Telegram 交流群</a>
                    </div>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <a href="https://discord.gg/tGQddPDh" target="_blank" rel="noopener noreferrer; noopener noreferrer" class="hidden lg:flex w-10 h-10 rounded-full bg-[#5865F2] items-center justify-center shadow-lg"><svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg></a><a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer; noopener noreferrer" class="hidden lg:flex w-10 h-10 rounded-full bg-blue-500 items-center justify-center shadow-lg"><svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.89 1.2-5.33 3.52-.5.35-.96.52-1.37.51-.45-.01-1.31-.26-1.95-.47-.78-.26-1.4-.4-1.35-.85.03-.23.35-.47.96-.71 3.76-1.63 6.27-2.71 7.52-3.24 3.58-1.48 4.32-1.74 4.81-1.75.11 0 .35.03.5.15.13.1.17.23.18.33.02.09.03.26.01.4z"/></svg></a>
                <a href="/reg.html" class="hidden sm:block bg-[#f4af47] text-[#1e0a27] px-6 py-2 rounded-full font-black text-xs hover:scale-105 transition-all shadow-xl">Code: nbjh</a>
                <button id="m-btn" class="lg:hidden p-1.5 text-[#f4af47] border border-[#f4af47]/20 rounded-lg"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg></button>
            </div>
        </nav>
    </header>
    <!-- 手机侧边栏 (重新设计) -->
    <div id="mobile-menu" class="fixed inset-0 z-[1000] lg:hidden" style="display:none;">
        <div id="m-overlay" class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
        <div id="m-panel" class="absolute top-0 right-0 bottom-0 w-[85%] max-w-sm bg-[#1e0a27] border-l border-white/10 overflow-y-auto" style="transform:translateX(100%);transition:transform 0.35s cubic-bezier(0.4,0,0.2,1);">
            <!-- 顶栏：Logo + 关闭 -->
            <div class="flex items-center justify-between p-5 border-b border-white/5">
                <div class="flex items-center gap-2">
                    <img alt="Pi" src="/static/favicon.png" class="w-8 h-8" loading="lazy">
                    <span class="text-sm font-black tracking-tight uppercase text-white">Pi 中文网</span>
                </div>
                <button id="m-close" class="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>

            <!-- 邀请码横幅 -->
            <div class="mx-4 mt-4 mb-2 bg-[#f4af47]/10 border border-[#f4af47]/20 rounded-xl px-4 py-3 flex items-center justify-between">
                <div>
                    <div class="text-[10px] font-bold text-[#f4af47]/60 uppercase tracking-widest">邀请码</div>
                    <div class="text-lg font-black text-[#f4af47] tracking-wide">nbjh</div>
                </div>
                <a href="/reg.html" class="bg-[#f4af47] text-[#1e0a27] px-4 py-2 rounded-lg font-black text-xs hover:scale-105 transition-transform">立即注册</a>
            </div>

            <!-- 导航列表 -->
            <nav class="p-4 space-y-1">
                <a href="/index.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🏠</span>
                    <span class="font-bold text-white">首页</span>
                </a>
                <a href="/price.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">💰</span>
                    <span class="font-bold text-[#f4af47]">派币实时价格</span>
                </a>

                <!-- Pi 区块链 -->
                <div class="mt-4 mb-2 px-4">
                    <div class="text-[10px] font-black tracking-widest text-gray-500 uppercase">Pi 区块链</div>
                </div>
                <a href="/nodes.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🖥️</span>
                    <span class="font-bold text-white">Pi 节点</span>
                </a>
                <a href="/blockchain.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🔍</span>
                    <span class="font-bold text-white">区块浏览器</span>
                </a>
                <a href="/technical-whitepaper.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">📄</span>
                    <span class="font-bold text-white">技术白皮书</span>
                </a>
                <a href="/roadmap.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🗺️</span>
                    <span class="font-bold text-white">项目路线图</span>
                </a>

                <!-- 生态系统 -->
                <div class="mt-4 mb-2 px-4">
                    <div class="text-[10px] font-black tracking-widest text-gray-500 uppercase">生态系统</div>
                </div>
                <a href="/developers.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">💻</span>
                    <span class="font-bold text-white">开发者中心</span>
                </a>
                <a href="/browser.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🌐</span>
                    <span class="font-bold text-white">Pi 浏览器</span>
                </a>
                <a href="/pi-shopping.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🛒</span>
                    <span class="font-bold text-white">Pi 购物</span>
                </a>

                
                <div class="mt-4 mb-2 px-4"><div class="text-[10px] font-black tracking-widest text-gray-500 uppercase">📚 Pi百科</div></div>
                <a href="/pi-guide.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">📚</span><span class="font-bold text-[#f4af47]">百科首页（全部教程）</span></a>
                <a href="/pi-download.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">📲</span><span class="font-bold text-white">下载安装</span></a>
                <a href="/mining-tutorial.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">⛏️</span><span class="font-bold text-white">挖矿教程</span></a>
                <a href="/wallet-guide.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">💳</span><span class="font-bold text-white">钱包交易</span></a>
                <a href="/pi-mainnet.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">🚀</span><span class="font-bold text-white">主网迁移</span></a>
                <a href="/kyc.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">✅</span><span class="font-bold text-white">KYC认证</span></a>
                <a href="/pi-legit.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"><span class="text-lg">🛡️</span><span class="font-bold text-white">安全与合规</span></a>

                <!-- 社区资讯 -->
                <div class="mt-4 mb-2 px-4">
                    <div class="text-[10px] font-black tracking-widest text-gray-500 uppercase">社区资讯</div>
                </div>
                <a href="/blog.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">📰</span>
                    <span class="font-bold text-white">官方新闻</span>
                </a>
                <a href="/pi-news.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">⚡</span>
                    <span class="font-bold text-white">Pi 最新动态</span>
                </a>
                <a href="/search.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">🔎</span>
                    <span class="font-bold text-white">搜索</span>
                </a>
                <a href="/faq.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">❓</span>
                    <span class="font-bold text-white">常见问题</span>
                </a>
                <a href="/about.html" class="mobile-nav-item flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors">
                    <span class="text-lg">ℹ️</span>
                    <span class="font-bold text-white">关于我们</span>
                </a>
            </nav>

            <!-- 底部社交 -->
            <div class="p-4 mt-auto border-t border-white/5">
                <div class="flex items-center gap-3">
                    <a href="https://discord.gg/tGQddPDh" target="_blank" rel="noopener noreferrer" class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#5865F2]/10 border border-[#5865F2]/20 text-[#5865F2] font-bold text-xs hover:bg-[#5865F2]/20 transition-colors">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/></svg>
                        Discord
                    </a>
                    <a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer" class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold text-xs hover:bg-blue-500/20 transition-colors">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.06.06 0 0 0-.02-.12c-.08-.06-.19-.04-.27-.02-.11.02-1.89 1.2-5.33 3.52-.5.35-.96.52-1.37.51-.45-.01-1.31-.26-1.95-.47-.78-.26-1.4-.4-1.35-.85.03-.23.35-.47.96-.71 3.76-1.63 6.27-2.71 7.52-3.24 3.58-1.48 4.32-1.74 4.81-1.75.11 0 .35.03.5.15.13.1.17.23.18.33.02.09.03.26.01.4z"/></svg>
                        Telegram
                    </a>
                </div>
            </div>
        </div>
    </div>


    <main class="max-w-3xl mx-auto pt-28 pb-20 px-6">
        {hero_image}
        <h1 class="text-4xl md:text-6xl font-black mb-4 tracking-tighter leading-tight">{title}</h1>
        <p class="text-gray-500 mb-10">{date}</p>
        <div class="prose max-w-none">
            {content}
        </div>
    </main>
    <footer class="py-12 bg-[#1a1220] text-center border-t border-white/5">
    <img alt="Pi Network Logo" src="/static/favicon.png" class="w-10 h-10 mb-6 mx-auto grayscale brightness-200" loading="lazy">
    <p class="text-sm font-bold text-gray-500 mb-6">© 2026 PI NETWORK 官方中文社区 · 邀请码: nbjh</p>
    <div class="flex flex-wrap justify-center gap-x-6 gap-y-3 text-sm font-bold text-gray-600 max-w-3xl mx-auto px-4">
        <a href="/reg.html" class="hover:text-[#f4af47]">Pi注册下载</a>
        <a href="/mining-tutorial.html" class="hover:text-white">手机挖矿教程</a>
        <a href="/wallet-guide.html" class="hover:text-white">钱包使用指南</a>
        <a href="/pi-guide.html" class="hover:text-[#f4af47]">📚 Pi百科</a>
        <a href="/price.html" class="hover:text-[#f4af47]">Pi实时价格</a>
        <a href="/kyc.html" class="hover:text-white">KYC认证教程</a>
        <a href="/pi-news.html" class="hover:text-white">Pi最新动态</a>
        <a href="/faq.html" class="hover:text-white">常见问题</a>
        <a href="/about.html" class="hover:text-white">关于我们</a>
    </div>
</footer>
<script>
(function(){{
    var mm=document.getElementById('mobile-menu'),
        mp=document.getElementById('m-panel'),
        mo=document.getElementById('m-overlay'),
        mb=document.getElementById('m-btn'),
        mc=document.getElementById('m-close');
    if(!mm||!mp||!mb||!mc) return;
    function open(){{mm.style.display='flex';requestAnimationFrame(function(){{mp.style.transform='translateX(0)';}});}}
    function close(){{mp.style.transform='translateX(100%)';setTimeout(function(){{mm.style.display='none';}},350);}}
    mb.onclick=open;
    mc.onclick=close;
    if(mo) mo.onclick=close;
}})();
</script>
</body>
</html>

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
    """翻译整篇文章，优先逐段 Google Translate，备用 LLM 整体翻译"""
    # 方法1: 逐段 Google Translate（免费，无需 API key）
    translated = []
    all_ok = True
    for i, p in enumerate(paragraphs):
        if p["type"] in ("img", "video"):
            translated.append(p)
            continue
        text = p["text"]
        # HTML 段落提取纯文本再翻译
        if text.startswith("<"):
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
        if not text or len(text.strip()) < 3:
            translated.append({"type": p["type"], "text": text})
            continue
        try:
            result = GoogleTranslator(source='en', target='zh-CN').translate(text)
            if result and len(result.strip()) > 0:
                translated.append({"type": p["type"], "text": result.strip()})
            else:
                translated.append({"type": p["type"], "text": text})
                all_ok = False
        except Exception as e:
            print(f"[!] Google翻译段落 {i} 失败: {e}")
            translated.append({"type": p["type"], "text": text})
            all_ok = False
        time.sleep(0.3)  # 避免请求过快

    # 中文检测
    chinese_count = sum(
        sum(1 for c in tp["text"] if '\u4e00' <= c <= '\u9fff')
        for tp in translated if tp["type"] not in ("img", "video")
    )
    total_chars = sum(
        len(tp["text"])
        for tp in translated if tp["type"] not in ("img", "video")
    )
    chinese_ratio = chinese_count / total_chars if total_chars > 0 else 0
    print(f"[✓] Google翻译完成，共 {len(translated)} 个段落，中文率 {chinese_ratio:.1%}")
    if chinese_ratio >= 0.05:
        return translated

    # 方法2: LLM 整体翻译（备用，需要 API key）
    if not LLM_API_KEY:
        print("[!] Google翻译中文率不足且无 LLM API key，跳过")
        return None

    # 构建 LLM prompt
    lines = []
    for i, p in enumerate(paragraphs):
        if p["type"] in ("img", "video"):
            lines.append(f"[{i}][{p['type'].upper()}] __SKIP__")
        else:
            text = p["text"]
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
                        text = result_lines.get(i, p["text"])
                        if text == "__SKIP__":
                            text = p["text"]
                        translated.append({"type": p["type"], "text": text})

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
                    print(f"[!] 翻译结果中文比例过低，判定为 API 失败，跳过本文")
                    return None
                return translated
            else:
                print(f"[!] LLM API 错误: HTTP {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"[!] 翻译失败 (尝试 {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(5)

    print("[!] 全部翻译方法失败，跳过本文")
    return None


def translate_text(text, max_retries=2):
    """单段文本翻译（用于标题），优先 Google Translate，备用 LLM"""
    if not text or len(text.strip()) < 3:
        return text
    # 方法1: Google Translate（免费，无需 API key）
    for attempt in range(max_retries + 1):
        try:
            result = GoogleTranslator(source='en', target='zh-CN').translate(text)
            if result and len(result.strip()) > 0:
                return result.strip()
        except Exception as e:
            print(f"[!] Google翻译失败 (尝试 {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(2)
    # 方法2: LLM API（备用，需要 API key）
    if LLM_API_KEY:
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
                print(f"[!] LLM翻译失败: HTTP {resp.status_code}")
            except Exception as e:
                print(f"[!] LLM翻译失败 (尝试 {attempt+1}): {e}")
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
        slug=slug,
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
