import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("[*] 正在模拟真人访问官网...")
        await page.goto("https://minepi.com/white-paper/", timeout=60000)
        
        # 等待正文渲染完成 (Salient 框架常用的容器)
        await page.wait_for_selector(".post-content", timeout=30000)
        
        # 抓取全量 HTML 源码
        content = await page.inner_html(".post-content")
        
        with open("raw_whitepaper_playwright.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"[*] 【奇迹发生】抓取成功！文件大小: {len(content)} 字节")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
