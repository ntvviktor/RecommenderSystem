import asyncio
import json
from playwright.async_api import async_playwright
from extract import extract
import urllib


def create_book_url(book_name: str) -> str:
    amazon_params = {"k": f"{book_name} book"}
    amazon_url = "https://www.amazon.sg/s?" + urllib.parse.urlencode(
        amazon_params, doseq=True
    )
    return amazon_url


async def main():
    books_data_url = []
    with open("book2scrape_v3.csv", "r") as f:
        book_data = f.readlines()

    count = 0
    for b in book_data:
        content = b.split("|")
        title = content[0].strip()
        isbn = content[1].strip()
        count += 1
        b = b.strip()
        b_url = create_book_url(title)
        books_data_url.append((b_url, isbn))
        if count == 205:
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
                await page.goto(url, timeout=0)  # 3 minutes

                await page.wait_for_selector(".s-result-list", timeout=0)
                first_element = await page.query_selector(".s-result-item.s-asin")

                if first_element:
                    detail_link = await first_element.query_selector("h2 a")
                    book_url = await detail_link.get_attribute("href")

                    await page.goto(f"https://www.amazon.sg{book_url}")
                    await page.wait_for_selector(".celwidget")

                    selectors = {
                        "title": "#productTitle",
                        "author": "#bylineInfo_feature_div",
                        "img": "#imgTagWrapperId",
                        "description": "#bookDescription_feature_div",
                        "price": ".a-color-price",
                        "details": "#detailBullets_feature_div",
                    }
                    data = {}
                    data["original_isbn"] = original_isbn
                    for key, selector in selectors.items():
                        element = await page.query_selector(selector)
                        if element:
                            if key == "price":
                                data[key] = await element.inner_text()
                            else:
                                data[key] = await element.inner_html()
                    data["url"] = f"https://www.amazon.sg{book_url}"
                    data["provider"] = "Amazon"

                    with open("data.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                    # Assuming extract is a function that processes the data
                    added_data = extract(data)
                    important_data.append(added_data)
                    print("Finishing...")
                    if len(important_data) == 50:
                        print("Number of data being scraped: ", count)
                    await page.close()
                    await asyncio.sleep(3)
        finally:
            await browser.close()
            with open("important.json", "w", encoding="utf-8") as f:
                json.dump(important_data, f, ensure_ascii=False, indent=4)

            print("Number of scraped data", len(important_data))
            print(count)


# Run the asynchronous main function
asyncio.run(main())
