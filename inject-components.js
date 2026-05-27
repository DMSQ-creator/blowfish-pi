/* ============================================
   inject-components.js
   全站导航栏 + 页脚 + 悬浮CTA 自动注入
   ============================================ */
(function(){
  const BASE = document.querySelector('meta[name="base"]')?.content || '.';

  /* ---- 导航栏 HTML ---- */
  const NAV_HTML = `
  <!-- 全局悬浮CTA -->
  <a href="${BASE}/reg.html" class="fixed-cta hidden lg:flex bg-[#f4af47] text-[#1e0a27] p-4 rounded-2xl font-black shadow-2xl items-center gap-3 border-4 border-[#1e0a27]">
    <span class="text-xl">🔥</span>
    <div class="text-[10px] font-black leading-none uppercase">注册教程</div>
  </a>

  <!-- 导航栏 -->
  <header class="fixed w-full z-[100] nav-blur border-b border-white/10">
    <nav class="text-white container mx-auto px-4 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" onclick="location.href='${BASE}/index.html'">
        <img alt="Pi Network Logo" src="${BASE}/static/favicon.png" class="w-10 h-10">
        <span class="text-xl font-black tracking-tighter uppercase whitespace-nowrap">Pi Network 中文网</span>
      </div>
      <!-- 桌面菜单 -->
      <div class="hidden lg:flex items-center gap-8">
        <a href="${BASE}/price.html" data-nav="price.html" class="text-[11px] font-black tracking-widest uppercase hover:text-[#f4af47] transition-colors">派币价格</a>
        <div class="dropdown relative group">
          <div class="text-[11px] font-black tracking-widest text-white uppercase cursor-pointer hover:text-[#f4af47] flex items-center gap-1">Pi 区块链 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
          <div class="dropdown-menu absolute hidden pt-4 w-48 left-0">
            <a href="${BASE}/nodes.html" data-nav="nodes.html">Pi 节点 (Node)</a>
            <a href="${BASE}/blockchain.html" data-nav="blockchain.html">区块浏览器</a>
            <a href="${BASE}/technical-whitepaper.html" data-nav="technical-whitepaper.html">技术白皮书</a>
            <a href="${BASE}/roadmap.html" data-nav="roadmap.html">项目路线图</a>
          </div>
        </div>
        <div class="dropdown relative group">
          <div class="text-[11px] font-black tracking-widest text-white uppercase cursor-pointer hover:text-[#f4af47] flex items-center gap-1">生态系统 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
          <div class="dropdown-menu absolute hidden pt-4 w-56 left-0">
            <a href="${BASE}/developers.html" data-nav="developers.html">开发者中心</a>
            <a href="${BASE}/browser.html" data-nav="browser.html">Pi 浏览器下载</a>
            <a href="${BASE}/kyc.html" data-nav="kyc.html">KYC 身份认证</a>
            <a href="${BASE}/mining-tutorial.html" data-nav="mining-tutorial.html">挖矿教程</a>
            <a href="${BASE}/wallet-guide.html" data-nav="wallet-guide.html">钱包交易</a>
          </div>
        </div>
        <a href="${BASE}/about.html" data-nav="about.html" class="text-[11px] font-black tracking-widest uppercase hover:text-[#f4af47] transition-colors">关于我们</a>
        <div class="dropdown relative group">
          <div class="text-[11px] font-black tracking-widest uppercase cursor-pointer hover:text-[#f4af47] flex items-center gap-1">社区资讯 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"></path></svg></div>
          <div class="dropdown-menu absolute hidden pt-4 w-52 left-0">
            <a href="${BASE}/blog.html" data-nav="blog.html">官方新闻动态</a>
            <a href="${BASE}/pi-news.html" data-nav="pi-news.html">Pi 最新动态</a>
            <a href="${BASE}/reg.html" data-nav="reg.html">保姆级注册教程</a>
            <a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer">Telegram 交流群</a>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <a href="https://discord.gg/tGQddPDh" target="_blank" rel="noopener noreferrer" class="hidden lg:flex w-10 h-10 rounded-full bg-[#5865F2] items-center justify-center shadow-lg"><svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg></a>
        <a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer" class="hidden lg:flex w-10 h-10 rounded-full bg-blue-500 items-center justify-center shadow-lg"><svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.06.06 0 0 0-.02-.12c-.08-.06-.19-.04-.27-.02-.11.02-1.89 1.2-5.33 3.52-.5.35-.96.52-1.37.51-.45-.01-1.31-.26-1.95-.47-.78-.26-1.4-.4-1.35-.85.03-.23.35-.47.96-.71 3.76-1.63 6.27-2.71 7.52-3.24 3.58-1.48 4.32-1.74 4.81-1.75.11 0 .35.03.5.15.13.1.17.23.18.33.02.09.03.26.01.4z"/></svg></a>
        <a href="${BASE}/reg.html" class="hidden sm:block bg-[#f4af47] text-[#1e0a27] px-6 py-2 rounded-full font-black text-xs hover:scale-105 transition-all shadow-xl">Code: nbjh</a>
        <button id="m-btn" class="lg:hidden p-1.5 text-[#f4af47] border border-[#f4af47]/20 rounded-lg"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg></button>
      </div>
    </nav>
  </header>

  <!-- 手机侧边栏 -->
  <div id="mobile-menu" class="fixed inset-0 z-[1000] bg-gradient-to-b from-[#1e0a27] to-[#423f88] lg:hidden flex flex-col p-10 overflow-y-auto">
    <button id="m-close" class="absolute top-6 right-6 p-2 text-[#f4af47] font-black text-lg">✕ CLOSE</button>
    <div class="flex flex-col gap-5 mt-16 text-2xl font-black uppercase text-white">
      <a href="${BASE}/index.html" class="text-[#f4af47]">首页</a>
      <div class="h-px bg-white/10 w-full"></div>
      <a href="${BASE}/price.html" class="hover:text-[#f4af47] transition-colors">派币实时价格</a>
      <a href="${BASE}/mining-tutorial.html" class="hover:text-[#f4af47] transition-colors">挖矿教程</a>
      <a href="${BASE}/wallet-guide.html" class="hover:text-[#f4af47] transition-colors">钱包交易</a>
      <div class="h-px bg-white/10 w-full"></div>
      <a href="${BASE}/technical-whitepaper.html" class="hover:text-[#f4af47] transition-colors">技术白皮书</a>
      <a href="${BASE}/nodes.html" class="hover:text-[#f4af47] transition-colors">Pi 节点运行</a>
      <a href="${BASE}/roadmap.html" class="hover:text-[#f4af47] transition-colors">发展路线图</a>
      <a href="${BASE}/kyc.html" class="hover:text-[#f4af47] transition-colors">身份认证 (KYC)</a>
      <div class="h-px bg-white/10 w-full"></div>
      <a href="${BASE}/blog.html" class="hover:text-[#f4af47] transition-colors">官方最新动态</a>
      <a href="${BASE}/pi-news.html" class="hover:text-[#f4af47] transition-colors">Pi 最新动态</a>
      <a href="${BASE}/faq.html" class="hover:text-[#f4af47] transition-colors">常见问题 (FAQ)</a>
      <a href="${BASE}/about.html" class="hover:text-[#f4af47] transition-colors">关于我们</a>
      <a href="${BASE}/search.html" class="hover:text-[#f4af47] transition-colors">🔍 搜索</a>
      <div class="h-px bg-white/10 w-full"></div>
      <a href="${BASE}/reg.html" class="text-[#f4af47] underline underline-offset-8 text-xl">🔥 注册下载教程</a>
    </div>
    <p class="text-center text-white/60 text-xs uppercase tracking-widest font-bold mt-auto">推荐邀请码: nbjh</p>
  </div>
  `;

  /* ---- 页脚 HTML ---- */
  const FOOTER_HTML = `
  <footer class="py-12 bg-[#252525] text-center border-t border-white/5">
    <img alt="Pi Network Logo" src="${BASE}/static/favicon.png" class="w-10 h-10 mb-6 mx-auto grayscale brightness-200">
    <div class="flex justify-center gap-6 mb-6">
      <a href="https://discord.gg/tGQddPDh" target="_blank" rel="noopener noreferrer" class="footer-social">
        <svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
      </a>
      <a href="https://t.me/+6tlAJx6e1081Mjhh" target="_blank" rel="noopener noreferrer" class="footer-social tg">
        <svg class="w-5 h-5" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.06.06 0 0 0-.02-.12c-.08-.06-.19-.04-.27-.02-.11.02-1.89 1.2-5.33 3.52-.5.35-.96.52-1.37.51-.45-.01-1.31-.26-1.95-.47-.78-.26-1.4-.4-1.35-.85.03-.23.35-.47.96-.71 3.76-1.63 6.27-2.71 7.52-3.24 3.58-1.48 4.32-1.74 4.81-1.75.11 0 .35.03.5.15.13.1.17.23.18.33.02.09.03.26.01.4z"/></svg>
      </a>
    </div>
    <p class="text-sm font-bold text-gray-400 mb-6">
      © 2026 Pi Network 中文网 · 邀请码 <span class="text-[#f4af47]">nbjh</span>
    </p>
    <div class="flex flex-wrap justify-center gap-8 text-sm font-bold text-gray-400">
      <a href="${BASE}/about.html" class="hover:text-white transition-colors">关于我们</a>
      <a href="${BASE}/technical-whitepaper.html" class="hover:text-white transition-colors">技术文档</a>
      <a href="${BASE}/reg.html" class="hover:text-[#f4af47] transition-colors">下载注册</a>
      <a href="${BASE}/nodes.html" class="hover:text-white transition-colors">节点运行</a>
      <a href="${BASE}/faq.html" class="hover:text-white transition-colors">常见问题</a>
    </div>
  </footer>
  `;

  /* ---- 注入 ---- */
  function inject() {
    // 注入导航
    const navEl = document.getElementById('site-nav');
    if (navEl) {
      navEl.innerHTML = NAV_HTML;
      navEl.classList.add('loaded');
    }

    // 注入页脚
    const footEl = document.getElementById('site-footer');
    if (footEl) {
      footEl.innerHTML = FOOTER_HTML;
      footEl.classList.add('loaded');
    }

    // 当前页面高亮
    const currentPage = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('[data-nav]').forEach(el => {
      if (el.getAttribute('data-nav') === currentPage) {
        el.classList.add('nav-active');
      }
    });

    // 手机菜单开关
    const mBtn = document.getElementById('m-btn');
    const mMenu = document.getElementById('mobile-menu');
    const mClose = document.getElementById('m-close');
    if (mBtn && mMenu) {
      mBtn.addEventListener('click', () => mMenu.classList.add('open'));
    }
    if (mClose && mMenu) {
      mClose.addEventListener('click', () => mMenu.classList.remove('open'));
    }
  }

  // DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
