import urllib.parse
import json
from extract import extract
from playwright.sync_api import sync_playwright
import time


def create_book_url(book_name: str) -> str:
    amazon_params = {"k": book_name}
    amazon_url = "https://www.amazon.sg/s?" + urllib.parse.urlencode(
        amazon_params, doseq=True
    )
    return amazon_url


"""
Example code for headers
headers = requests.utils.default_headers()
headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
})

amazon_page = requests.get(amazon_url, headers=headers)
soup = BeautifulSoup(amazon_page.content, "html.parser")
"""

books_data_url = []
with open("../books/book2scrape_v2.csv", "r") as f:
    book_data = f.readlines()

count = 0
for b in book_data:
    count += 1
    b = b.strip()
    b_url = create_book_url(b)
    books_data_url.append(b_url)
    if count == 50:
        break

important_data = []

with sync_playwright() as pw:
    try:
        # create browser instance
        browser = pw.chromium.launch(
            # we can choose either a Headful (With GUI) or Headless mode:
            headless=True,
        )
        # create context
        # using context we can define page properties like viewport dimensions
        context = browser.new_context(
            # most common desktop viewport is 1920x1080
            viewport={"width": 1920, "height": 1080}
        )
        for url in books_data_url:
            print("Starting to scrape")
            # create page aka browser tab which we'll be using to do everything
            page = context.new_page()
            page.goto(url, timeout=60 * 3 * 1000)

            page.wait_for_selector(".s-result-list")
            first_element = page.query_selector(".s-result-item.s-asin")

            if first_element:
                detail_link = first_element.query_selector("h2 a")
                book_url = detail_link.get_attribute("href")
                # print(book_url)

                page.goto(f"https://www.amazon.sg{book_url}")
                page.wait_for_selector(".celwidget")

                titleId = "#productTitle"
                authorId = "#bylineInfo_feature_div"
                bookImgWrapperId = "#imgTagWrapperId"
                bookDescriptionId = "#bookDescription_feature_div"
                priceClassName = ".a-color-price"
                reviewsId = "#editorialReviews_feature_div"
                productDetailsId = "#detailBullets_feature_div"

                titleHTML = page.query_selector(titleId)
                if titleHTML:
                    titleHTML = titleHTML.inner_html()

                authorHTML = page.query_selector(authorId)
                if authorHTML:
                    authorHTML = authorHTML.inner_html()

                bookImgHTML = page.query_selector(bookImgWrapperId)
                if bookImgHTML:
                    bookImgHTML = bookImgHTML.inner_html()

                bookDescriptionHTML = page.query_selector(bookDescriptionId)
                if bookDescriptionHTML:
                    bookDescriptionHTML = bookDescriptionHTML.inner_html()

                priceHTML = page.query_selector(priceClassName)
                if priceHTML:
                    price = priceHTML.inner_text()
                else:
                    price = None

                reviewsHTML = page.query_selector(reviewsId)
                if reviewsHTML:
                    reviewsHTML = reviewsHTML.inner_html()

                productDetailsHTML = page.query_selector(productDetailsId)
                if productDetailsHTML:
                    productDetailsHTML = productDetailsHTML.inner_html()
                data = {
                    "title": titleHTML,
                    "author": authorHTML,
                    "img": bookImgHTML,
                    "description": bookDescriptionHTML,
                    "price": price,
                    "reviews": reviewsHTML,
                    "details": productDetailsHTML,
                    "url": f"https://www.amazon.sg{book_url}",
                    "provider": "Amazon",
                }
                with open("data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                added_data = extract(data)
                important_data.append(added_data)
                print("Finishing...")
                page.close()
                time.sleep(5)
    finally:
        browser.close()
        with open("important.json", "w", encoding="utf-8") as f:
            json.dump(important_data, f, ensure_ascii=False, indent=4)

        print(count)
