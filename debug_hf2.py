"""Debug: trace what *direct children* of main are, and which ones trigger skip."""
import asyncio, re
from bs4 import BeautifulSoup, Tag, NavigableString
from webdown.infrastructure.services.playwright_page_renderer import render

url = "https://huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr"
html = render(url)
soup = BeautifulSoup(html, "lxml")

main = soup.find("article") or soup.find("main") or soup.find("body")
print(f"main tag: <{main.name}>")
print(f"main class: {' '.join(main.get('class', []))[:100]}")
print()

# Show direct children
print("=== DIRECT CHILDREN OF MAIN ===")
for i, child in enumerate(main.find_all(recursive=False)):
    if isinstance(child, Tag):
        name = child.name
        cls = " ".join(child.get("class", []))[:80]
        text_len = len(child.get_text(strip=True))
        aria = (child.get("aria-label") or "")[:60]
        role = (child.get("role") or "")[:60]
        print(f"  [{i}] <{name}> class={cls!r} text_len={text_len} aria={aria!r} role={role!r}")
        
        # Check if it matches breadcrumb detection
        if "breadcrumb" in aria.lower() or "breadcrumb" in cls.lower():
            print(f"       ** BREADCRUMB MATCH **")
        
        # Check last-updated
        text = (child.get_text(" ", strip=True) or "").lower()
        if "last updated" in text or "last modified" in text:
            print(f"       ** LAST-UPDATED MATCH: {text[:100]} **")
        
        # Check alert
        alert_words = ["admonition", "alert", "callout", "theme-doc-alert"]
        for w in alert_words:
            if w in cls.lower():
                print(f"       ** ALERT MATCH: {w} **")
        for w in ["note", "warning", "tip", "danger", "info"]:
            if w in cls.lower() and any(a in cls.lower() for a in alert_words):
                print(f"       ** ALERT TYPE: {w} **")
    else:
        text = str(child).strip()[:80]
        if text:
            print(f"  [{i}] <text> {text}")
