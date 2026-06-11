#!/usr/bin/env python3
"""
批量翻译已有但未翻译的博文 v2 - 使用正则直接替换 prose div 内容
"""
import re, os, time
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

BLOG_DIR = "blog"

UNTRANSLATED = [
    "app-studio-code",
    "app-studio-event-payments-ads",
    "dex-amm-token-creation",
    "fast-track-kyc",
    "hackathon-2025-winners",
    "holiday-commerce-raffle",
    "kyc-ai-integration",
    "open-network-update",
    "openmind-case-study",
    "pi-cidi-games",
    "pi-hackathon-2025",
    "pi-linux-node",
    "pi-network-ventures-openmind",
    "pi-node-0-5-4",
    "pi2day-2025-recap",
    "pi2day2025",
    "wallet-activation",
]

def translate_text(text):
    """Translate text using GoogleTranslator"""
    if not text.strip():
        return ""
    
    MAX_LEN = 4500
    translator = GoogleTranslator(source='en', target='zh-CN')
    
    if len(text) <= MAX_LEN:
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"  [!] Translation error: {e}")
            return None
    
    # Split by double newlines
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) > MAX_LEN and current:
            chunks.append(current)
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current:
        chunks.append(current)
    
    translated = []
    for i, chunk in enumerate(chunks):
        print(f"  Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            result = translator.translate(chunk)
            translated.append(result)
        except Exception as e:
            print(f"  [!] Chunk {i+1} error: {e}")
            return None
        time.sleep(1)
    
    return "\n\n".join(translated)

def extract_text_from_html(html_content):
    """Extract plain English text from the messy Visual Composer HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    text_parts = []
    for el in soup.find_all(["p", "h2", "h3", "h4"]):
        text = el.get_text(strip=True)
        if text:
            if el.name in ("h2", "h3", "h4"):
                text_parts.append(f"[{el.name.upper()}] {text}")
            else:
                text_parts.append(text)
    
    # Also handle list items
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text and not any(text in part for part in text_parts):
            text_parts.append(f"- {text}")
    
    return "\n\n".join(text_parts)

def process_blog_post(slug):
    filepath = os.path.join(BLOG_DIR, f"{slug}.html")
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return False
    
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Find the prose div content using regex
    # Pattern: <div class="prose max-w-none"> ... </div>
    prose_match = re.search(
        r'(<div class="prose max-w-none">)(.*?)(</div>)\s*\n\s*<!-- AdSense',
        html, re.DOTALL
    )
    
    if not prose_match:
        # Try alternate pattern (prose followed by main close)
        prose_match = re.search(
            r'(<div class="prose max-w-none">)(.*?)(</div>)\s*\n\s*</main>',
            html, re.DOTALL
        )
    
    if not prose_match:
        print(f"[!] Could not find prose div in {slug}")
        # Debug: show what's around prose
        idx = html.find('class="prose')
        if idx >= 0:
            print(f"  Context: ...{html[idx:idx+200]}...")
        return False
    
    prose_prefix = prose_match.group(1)
    prose_content = prose_match.group(2)
    prose_suffix = prose_match.group(3)
    
    # Extract English text from the messy HTML
    english_text = extract_text_from_html(prose_content)
    if not english_text:
        print(f"[!] No text extracted from {slug}")
        return False
    
    print(f"  Extracted {len(english_text)} chars of English text")
    
    # Translate
    translated = translate_text(english_text)
    if translated is None:
        return False
    
    # Convert to clean HTML
    html_parts = []
    for line in translated.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[H2] "):
            html_parts.append(f"<h2>{line[5:]}</h2>")
        elif line.startswith("[H3] "):
            html_parts.append(f"<h3>{line[5:]}</h3>")
        elif line.startswith("[H4] "):
            html_parts.append(f"<h4>{line[5:]}</h4>")
        elif line.startswith("- ") or line.startswith("• "):
            content = line[2:]
            html_parts.append(f"<p>• {content}</p>")
        else:
            html_parts.append(f"<p>{line}</p>")
    
    new_prose_content = "\n            ".join(html_parts)
    
    # Build replacement
    old_block = prose_match.group(0)
    new_block = f'{prose_prefix}\n            {new_prose_content}\n        {prose_suffix}'
    
    new_html = html.replace(old_block, new_block)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_html)
    
    print(f"  ✅ {slug} translated and saved")
    return True

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    success = 0
    failed = 0
    for slug in UNTRANSLATED:
        print(f"\n{'='*60}")
        print(f"Processing: {slug}")
        print(f"{'='*60}")
        
        if process_blog_post(slug):
            success += 1
        else:
            failed += 1
        time.sleep(2)
    
    print(f"\n\nDone! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
