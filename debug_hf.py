"""Debug script: render a HF blog page and dump the HTML for analysis."""
import asyncio
import sys
sys.path.insert(0, ".")

from webdown.infrastructure.services.playwright_page_renderer import render

url = sys.argv[1] if len(sys.argv) > 1 else "https://huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr"
print(f"Rendering: {url}")
html = render(url)
print(f"\nHTML length: {len(html)} chars")
print(f"\nFirst 3000 chars:\n{html[:3000]}")
print(f"\nLast 3000 chars:\n{html[-3000:]}")

# Also check for key content markers
import re
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "lxml")

# Check for article/main content areas
for tag_name in ["article", "main", "section", "div"]:
    tags = soup.find_all(tag_name)
    for t in tags:
        cls = " ".join(t.get("class", []))[:80]
        text_len = len(t.get_text(strip=True))
        if text_len > 200:
            print(f"\n[{tag_name}] class='{cls}' text_len={text_len}")

# Check for heading structure
for level in range(1, 7):
    headings = soup.find_all(f"h{level}")
    for h in headings:
        print(f"  h{level}: {h.get_text(strip=True)[:100]}")
