#!/usr/bin/env bash
#
# 📝 Pi 中文网一键发文脚本
# 用法: bash publish.sh
# 交互式填写标题、日期、分类、摘要、正文，自动生成文章页并更新 blog.html
#

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BLOG_DIR="$REPO_DIR/blog"
BLOG_HTML="$REPO_DIR/blog.html"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   📝 Pi Network 中文网 · 一键发文工具    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 输入信息 ──
read -rp "📌 文章标题: " TITLE
[ -z "$TITLE" ] && echo "❌ 标题不能为空" && exit 1

read -rp "📅 日期 (格式 2026.03.20，回车默认今天): " DATE_INPUT
if [ -z "$DATE_INPUT" ]; then
    DATE_INPUT=$(date +%Y.%m.%d)
fi

read -rp "📂 分类 (如：官方公告/技术更新/社区动态，回车默认'官方公告'): " CATEGORY
[ -z "$CATEGORY" ] && CATEGORY="官方公告"

read -rp "📝 摘要 (一两句话): " SUMMARY
[ -z "$SUMMARY" ] && echo "❌ 摘要不能为空" && exit 1

# 文件名：从标题生成 slug
SLUG=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9\u4e00-\u9fff]/-/g; s/--*/-/g; s/^-//; s/-$//' | head -c 60)
# 如果标题全是中文，用拼音或日期做文件名
if [ -z "$SLUG" ] || [ "$SLUG" = "-" ]; then
    SLUG="article-$(date +%Y%m%d-%H%M%S)"
fi
read -rp "📄 文件名 (回车默认: $SLUG): " SLUG_INPUT
[ -n "$SLUG_INPUT" ] && SLUG="$SLUG_INPUT"

ARTICLE_FILE="$BLOG_DIR/$SLUG.html"
if [ -f "$ARTICLE_FILE" ]; then
    echo "⚠️  文件已存在: $ARTICLE_FILE"
    read -rp "是否覆盖？(y/N): " OVERWRITE
    [ "$OVERWRITE" != "y" ] && echo "已取消" && exit 0
fi

echo ""
echo "📖 现在输入正文（支持多行）。"
echo "   输入完成后按 Ctrl+D（或单独一行输入 EOF）结束："
echo "─────────────────────────────────────────"

BODY=""
while IFS= read -r line; do
    [ "$line" = "EOF" ] && break
    BODY="${BODY}${line}
"
done

[ -z "$BODY" ] && echo "❌ 正文不能为空" && exit 1

# ── 将正文按段落转为 HTML ──
BODY_HTML=""
while IFS= read -r para; do
    trimmed=$(echo "$para" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -z "$trimmed" ] && continue
    # 转义 HTML 特殊字符
    escaped=$(echo "$trimmed" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    BODY_HTML="${BODY_HTML}            <p>${escaped}</p>
"
done <<< "$BODY"

# ── 生成文章页 ──
cat > "$ARTICLE_FILE" << HTMLEOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${TITLE} | Pi Network 中文网</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f021a; color: white; line-height: 2.2; font-family: sans-serif; text-align: justify; }
        .text-pi-gold { background: linear-gradient(90deg, #f4af47 0%, #fab44b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .prose h2 { font-size: 2.2rem; font-weight: 900; margin: 4rem 0 2rem; color: #f4af47; border-left: 6px solid #f4af47; padding-left: 1.5rem; }
        .prose h3 { font-size: 1.6rem; font-weight: 800; margin: 2.5rem 0 1.2rem; color: #fff; }
        .prose p { margin-bottom: 2rem; font-size: 1.2rem; color: #cbd5e1; }
        .prose ul { list-style: disc; margin-left: 2.5rem; margin-bottom: 2.5rem; }
        .prose li { margin-bottom: 1rem; color: #cbd5e1; }
        .img-wrap { margin: 4rem 0; border-radius: 40px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="min-h-screen">
    <nav class="p-6 border-b border-white/5 bg-[#0f021a]/90 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-4xl mx-auto flex justify-between items-center"><a href="../blog.html" class="font-bold">← 返回列表</a><span class="text-[#f4af47] font-black uppercase">FULL ARTICLE</span></div>
    </nav>

    <main class="max-w-3xl mx-auto py-20 px-6">
        <h1 class="text-5xl md:text-7xl font-black mb-10 tracking-tighter leading-tight"><span class="text-pi-gold italic">${TITLE}</span></h1>
        <p class="text-sm text-gray-500 font-bold uppercase tracking-widest mb-20">发布于: ${DATE_INPUT} · ${CATEGORY}</p>

        <div class="prose">
${BODY_HTML}
        </div>
    </main>

    <footer class="py-24 text-center border-t border-white/5 opacity-50 text-xs">
        © 2026 PI NETWORK 中文社区门户网 · 邀请码: nbjh
    </footer>
</body>
</html>
HTMLEOF

echo ""
echo "✅ 文章页已生成: $ARTICLE_FILE"

# ── 更新 blog.html（在 blog-grid 最前面插入卡片） ──
CARD="            <!-- ${DATE_INPUT} -->\n            <a href=\"blog/${SLUG}.html\" class=\"blog-card block\">\n                <div class=\"text-[#f4af47] font-bold mb-4\">${DATE_INPUT} · ${CATEGORY}</div>\n                <h2 class=\"text-3xl font-bold mb-4\">${TITLE}</h2>\n                <p class=\"text-gray-500 mb-6 text-sm\">${SUMMARY}</p>\n            </a>"

# 在 id="blog-grid" 后面的下一行插入
sed -i "/<div id=\"blog-grid\"/a\\${CARD}" "$BLOG_HTML"

echo "✅ blog.html 已更新（新卡片已插入列表最前面）"

# ── 提交推送 ──
echo ""
read -rp "🚀 是否立即 git 提交并推送？(Y/n): " DO_PUSH
if [ "$DO_PUSH" != "n" ] && [ "$DO_PUSH" != "N" ]; then
    cd "$REPO_DIR"
    git add .
    git commit -m "📝 新增文章: ${TITLE}"
    git push origin main
    echo ""
    echo "✅ 已推送到 GitHub Pages！1-2 分钟后生效。"
    echo "   文章地址: https://pibizh.com/blog/${SLUG}.html"
    echo "   博客列表: https://pibizh.com/blog.html"
    echo "   首页自动更新 ✓"
else
    echo ""
    echo "⏸️  未推送。你可以手动执行:"
    echo "   cd $REPO_DIR && git add . && git commit -m '新增文章' && git push origin main"
fi

echo ""
echo "🎉 完成！"
