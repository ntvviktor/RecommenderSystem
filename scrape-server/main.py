from playwright.sync_api import sync_playwright, Playwright
import urllib
import json
from extract import extract

AUTH = "brd-customer-hl_d5e3d0ef-zone-scraping_browser1:16ys88s6446h"
SBR_WS_CDP = f"wss://{AUTH}@brd.superproxy.io:9222"


def create_book_url(book_name: str) -> str:
    amazon_params = {"k": book_name}
    amazon_url = "https://www.amazon.sg/s?" + urllib.parse.urlencode(
        amazon_params, doseq=True
    )
    return amazon_url


def run(pw: Playwright):
    print("Connecting to Scraping Browser")
    browser = pw.chromium.connect_over_cdp(SBR_WS_CDP)
    try:
        books_data_url = []
        with open("../books/book2scrape_v2.csv", "r") as f:
            book_data = f.readlines()

        count = 0
        for b in book_data:
            count += 1
            b = b.strip()
            b_url = create_book_url(b)
            books_data_url.append(b_url)
            if count == 100:
                break

        important_data = []

        for url in books_data_url:
            print("Connected! Navigating...")
            page = browser.new_page()
            page.goto(url, timeout=60 * 5 * 1000)
            print("Navigated! Scraping page content...")
            # CAPTCHA solving: If you know you are likely to encounter a CAPTCHA on your target page
            # client = page.context.new_cdp_session(page)
            # solve_result = client.send("Captcha.solve", {"detectTimeout": 30 * 1000})
            # status = solve_result["status"]
            # print(f"Captcha solve status: {status}")

            page.locator(".s-result-list")
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

                productDetailsHTML = page.query_selector(productDetailsId)
                if productDetailsHTML:
                    productDetailsHTML = productDetailsHTML.inner_html()

                data = {
                    "title": titleHTML,
                    "author": authorHTML,
                    "img": bookImgHTML,
                    "description": bookDescriptionHTML,
                    "price": price,
                    "details": productDetailsHTML,
                    "url": f"https://www.amazon.sg{book_url}",
                    "provider": "Amazon",
                }

                page.close()
                added_data = extract(data)
                important_data.append(added_data)
                print("Finishing...")

    finally:
        with open("important.json", "w", encoding="utf-8") as f:
            json.dump(important_data, f, ensure_ascii=False, indent=4)

        print(count)
        browser.close()


def main():
    with sync_playwright() as playwright:
        run(playwright)


if __name__ == "__main__":
    main()
