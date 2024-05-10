import asyncio
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import urllib

"""
Search Engine of Amazon and others are different, some adding 'book' keyword will be better
"""

def create_book_url(book_name: str) -> str:
    url_params = {"str": f"{book_name}"}
    opentrolley_url = "https://opentrolley.com.sg/Search.aspx?" + urllib.parse.urlencode(
        url_params, doseq=True
    ) + "&page=1&pgsz=20"
    return opentrolley_url

async def main():
    books_data_url = []
    with open("book2scrape_v3.csv", "r") as f:
        book_data = f.readlines()

    count = 0
    for b in book_data:
        content = b.split("|")
        isbn = content[0].strip()
        title = content[1].strip()
        count += 1
        b = b.strip()
        b_url = create_book_url(title)
        books_data_url.append((b_url, isbn))
        if count == 500:
            break

    async with async_playwright() as pw:
        # Create an instance of a headless Chromium browser
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        important_data = []

        try:
            for url, original_isbn in books_data_url:
                print("Starting to scrape")
                page = await context.new_page()
                await page.goto(url, timeout=0)

                first_element = await page.query_selector(".book.w3-row")
                data = {}
                if first_element is not None:
                    data["original_isbn"] = original_isbn
                    detail_link = await first_element.query_selector("a")
                    book_url = await detail_link.get_attribute("href")
                    img_tag = await first_element.query_selector("img")
                    element = await first_element.query_selector(".price-after-disc")
                    price = await element.inner_text() if element else ""
                    data["img"] = await img_tag.get_attribute("src")
                    data["price"] = price
                    data["url"] = f"https://opentrolley.com.sg/{book_url}"
                    data["provider"] = "OpenTrolley"

                    important_data.append(data)
                    
                    print("Finishing...")
                else:
                    data["original_isbn"] = original_isbn
                    data["img"] = ""
                    data["price"] = ""
                    data["url"] = ""
                    data["provider"] = "OpenTrolley"
                    print(url)
                    important_data.append(data)
                    continue
                    
                
                with open("important_parralel.json", "w", encoding="utf-8") as f:
                    json.dump(important_data, f, ensure_ascii=False, indent=4)
                    
                await page.close()
                await asyncio.sleep(3)

        finally:
            await browser.close()
            with open("important_parralel.json", "w", encoding="utf-8") as f:
                json.dump(important_data, f, ensure_ascii=False, indent=4)

            print("Number of scraped data", len(important_data))
            print(count)

asyncio.run(main())