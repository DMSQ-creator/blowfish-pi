#!/usr/bin/env python3
"""Fix missing </header> tags in broken HTML files."""

import re
import os

BROKEN_FILES = [
    "pi-account-recovery.html",
    "pi-download.html",
    "pi-identity-verify.html",
    "pi-legal.html",
    "pi-lockup.html",
    "pi-migration.html",
    "pi-mining-calculator.html",
    "pi-price-prediction.html",
    "pi-registration-issues.html",
    "pi-security-circle.html",
    "pi-shopping.html",
    "pi-withdraw.html",
]

# Read the correct nav template from index.html
with open("index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

# Extract from "<!-- 导航栏" to just before the breadcrumb div
# In index.html, the structure is: nav block -> </header> -> mobile-menu -> (breadcrumb is elsewhere)
# We need the entire nav + mobile menu block

# Find the nav start marker
nav_start = index_html.index("<!-- 导航栏")
# Find the end: the closing of mobile-menu div + the script that follows
# Look for the pattern right before the main content

# In index.html, after the mobile menu, there's a section or some content
# Let's find the closing of the mobile-menu div
mobile_menu_start = index_html.index('<div id="mobile-menu"', nav_start)
# Find the closing </div> for mobile-menu - it's 2 levels deep
# Actually, let me just find everything from nav_start to just before the main page content

# The mobile menu ends with </div> and then comes a <section or other content
# Let me find the pattern: after mobile-menu, the next significant element
# Search for the breadcrumb pattern that starts the content area

# Strategy: extract the full nav block from index.html (from <!-- 导航栏 to just before any page-specific content)
# In index.html, after mobile menu closes, the next element is the main section
# We want everything up to (but not including) the first <section or the hero area

# Find where mobile menu div closes - it's right before the page content
# In the working pages, the pattern is:
# </div>  (closing mobile-menu)
# then the page-specific content starts

# Let me find the mobile menu closing by counting divs
pos = mobile_menu_start
depth = 0
while pos < len(index_html):
    open_match = re.search(r'<div[\s>]', index_html[pos:])
    close_match = re.search(r'</div>', index_html[pos:])
    
    if close_match is None:
        break
    
    if open_match and open_match.start() < close_match.start():
        depth += 1
        pos += open_match.end()
    else:
        depth -= 1
        pos += close_match.end()
        if depth == 0:
            # This is the closing </div> of mobile-menu
            break

# Now find what comes after - skip whitespace and get the template end
# After the mobile menu, there might be a script or directly the content
template_end = pos

# The template is everything from nav_start to template_end
nav_template = index_html[nav_start:template_end]

# Verify the template contains </header>
assert "</header>" in nav_template, "Template must contain </header>!"

print(f"Nav template length: {len(nav_template)} chars")
print(f"Template starts with: {nav_template[:50]}")
print(f"Template contains </header>: {'</header>' in nav_template}")

# Now fix each broken file
for fname in BROKEN_FILES:
    if not os.path.exists(fname):
        print(f"SKIP: {fname} not found")
        continue
    
    with open(fname, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Find the nav start in the broken file
    if "<!-- 导航栏" in html:
        broken_nav_start = html.index("<!-- 导航栏")
    elif '<header class="fixed w-full z-[100]' in html:
        broken_nav_start = html.index('<header class="fixed w-full z-[100]')
    else:
        print(f"SKIP: {fname} - no nav marker found")
        continue
    
    # Find where the content starts - look for the breadcrumb or first <section
    # The breadcrumb is: <div class="container mx-auto px-6 py-3"><nav class="breadcrumb">
    breadcrumb_match = re.search(r'<div class="container mx-auto px-6 py-3"><nav class="breadcrumb">', html)
    section_match = re.search(r'<section class="py-12 px-6">', html)
    
    if breadcrumb_match:
        content_start = breadcrumb_match.start()
    elif section_match:
        content_start = section_match.start()
    else:
        print(f"SKIP: {fname} - no content marker found")
        continue
    
    # Replace the broken nav block with the correct template
    new_html = html[:broken_nav_start] + nav_template + "\n\n    " + html[content_start:]
    
    with open(fname, "w", encoding="utf-8") as f:
        f.write(new_html)
    
    # Verify
    has_header_close = "</header>" in new_html
    print(f"FIXED: {fname} - </header> present: {has_header_close}")

print("\nDone!")
