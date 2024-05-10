import asyncio
import json
from playwright.async_api import async_playwright
import urllib.parse


AUTH = 'brd-customer-hl_d5e3d0ef-zone-scraping_browser2:skbg7f6ycion'  
SBR_WS_CDP = f'wss://{AUTH}@brd.superproxy.io:9222'  

'''
https://www.lazada.sg/catalog/?spm=a2o42.home-sg.search.d_go&q=The%20Hunger%20Games
'''
def create_book_url(book_name: str) -> str:
    amazon_params = {"q": f"{book_name} book"}
    amazon_url = "https://www.lazada.sg/books-online/?" + urllib.parse.urlencode(
        amazon_params, doseq=True
    )
    amazon_url = amazon_url.replace("+", " ")
    
    return amazon_url


async def main():
    books_data_url = []
    important_data = []
    
    with open("books_title_to_scrape_isbn.csv", "r") as f:
        book_data = [line.strip().split("|") for line in f.readlines()][:100]

    for isbn, title in book_data:
        books_data_url.append((create_book_url(title.strip()), isbn.strip()))

    async with async_playwright() as pw:
        print("Starting...")
        browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP) 
        browser.con
        batch_size = 20
        tasks = []
        for i in range(0, len(books_data_url), batch_size):
            batch = books_data_url[i:i + batch_size]
            tasks.append(process_batch(browser, batch))

        results = await asyncio.gather(*tasks)
        for result in results:
            important_data.extend(result)

        await browser.close()
        with open("important.json", "w", encoding="utf-8") as f:
            json.dump(important_data, f, ensure_ascii=False, indent=4)

        print("Number of scraped data:", len(important_data))

async def process_batch(browser, batch):
    return await asyncio.gather(*(process_page(browser, url, isbn) for url, isbn in batch))


async def process_page(browser, url, isbn):
    data = {"original_isbn": isbn, "img": "", "price": "", "url": "", "provider": "Lazada"}
    try:
        page = await browser.new_page()
        await page.goto(url, timeout=2*60*1000)
        
        await page.wait_for_selector(".Ms6aG")
        first_element = await page.query_selector(".Ms6aG")
        if first_element:
            detail_link = await first_element.query_selector("a")
            book_url = await detail_link.get_attribute("href")
            img_tag = await first_element.query_selector("img")
            element = await page.query_selector(".ooOxS")
            price = await element.inner_text() if element else ""
            
            data.update({
                "img": await img_tag.get_attribute("src"),
                "price": price,
                "url": f"https:{book_url}"
            })
    except Exception as e:
        print(f"Failed to process {url}: {str(e)}")
    finally:
        await page.close()
    return data
# Run the asynchronous main function
asyncio.run(main())
