import asyncio
import os
from pyppeteer import launch

INPUT_DIR = "docs_raw"
OUTPUT_DIR = "docs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


async def extract_from_file(file_path, output_path):
    browser = await launch(headless=True, args=["--allow-file-access-from-files"])
    page = await browser.newPage()


    file_url = f"file:///{os.path.abspath(file_path)}".replace("\\", "/")
    print(f"🔍 Loading: {file_url}")
    await page.goto(file_url)
    
    # Only keep the first HTML part (ignore images/CSS in mhtml)
    html_start = content.find("<html")
    html_end = content.rfind("</html>") + len("</html>")
    html_content = content[html_start:html_end]

    soup = BeautifulSoup(html_content, "lxml")

    # Remove nav, footer, scripts etc.
    for tag in soup(["nav", "footer", "script", "style", "noscript"]):
        tag.decompose()

    # Use html2text for markdown-like formatting
    h = html2text.HTML2Text()
    h.ignore_links = False
    text = h.handle(str(soup.body))

    return text.strip()


# Process all .mhtml files
for filename in os.listdir(SOURCE_FOLDER):
    if filename.endswith(".mhtml"):
        filepath = os.path.join(SOURCE_FOLDER, filename)
        print(f"🔍 Extracting: {filename}")

        try:
            text = extract_text_from_mhtml(filepath)
            out_path = os.path.join(OUTPUT_FOLDER, filename.replace(".mhtml", ".txt"))

            with open(out_path, "w", encoding="utf-8") as out_file:
                out_file.write(text)

            print(f"✅ Saved: {out_path} ({len(text.splitlines())} lines)")

        except Exception as e:
            print(f"❌ Failed to extract {filename}: {e}")
