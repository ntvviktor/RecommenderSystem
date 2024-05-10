from bs4 import BeautifulSoup


def extract(data: dict):
    useful_info = {}

    "Extract information from the parser"
    for k, v in data.items():
        if v is None:
            continue
        if k == "original_isbn" or k == "url" or k == "provider":
            useful_info[k] = v
            continue

        try:
            html = BeautifulSoup(v, "html.parser")
            text = html.text.strip()
        except TypeError:
            print(data)
            print(v)
            continue

        if k == "author":
            authors = text.split("\n")
            try:
                useful_info[k] = authors[1]
            except IndexError:
                useful_info[k] = authors
        elif k == "img":
            tag = html.img
            attributes = tag.attrs
            useful_info[k] = attributes["src"]
        elif k == "description":
            useful_info[k] = text[:-9].strip()
        elif k == "price":
            useful_info[k] = text
        elif k == "reviews":
            useful_info[k] = "".join(html.text.splitlines()).strip()
        elif k == "details":
            product_details = {}
            # Extracting details
            # ASIN
            elements = html.find_all(attrs={"class": "a-list-item"})[:5]
            for _, element in enumerate(elements):
                sub_data = element.text.strip()
                a = sub_data.split(":")
                try:
                    key = a[0].replace("\u200f", "").replace("\n", "").strip()
                    val = a[1].replace("\u200e", "").replace("\n", "").strip()
                    product_details[key] = val
                except (IndexError, TypeError):
                    product_details = a

            useful_info["details"] = product_details

        else:
            useful_info[k] = text

    return useful_info
