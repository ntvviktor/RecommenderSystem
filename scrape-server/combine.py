import json
import csv
import pandas as pd

data = []

"""COMBINE script
with open(f"important.json", "r") as f:
    temp = json.load(f)
    data += temp
    
with open(f"books2scrape_WeiJie.json", "r") as f:
    temp = json.load(f)
    data += temp

with open("final.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(len(data))
"""

# with open("final.json", "r") as f:
#     json_data = json.load(f)
#     seen = []
#     unique = []
#     a = []
#     for i, v in enumerate(json_data):
#         a.append(v["original_isbn"])
#         if(v["original_isbn"] == "isbn"):
#             json_data.pop(i)
#         elif v["original_isbn"] not in unique:
#             unique.append(v["original_isbn"])
#         else:
#             seen.append(v["original_isbn"])
#             json_data.pop(i)


# with open("final.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)

# with open("lazada_data.json", "r") as f:
#     json_data = json.load(f)

# csv_file = "output.csv"
# with open(csv_file, "w") as f:
#     csv_writer = csv.writer(f)
#     headers = json_data[0].keys()
#     csv_writer.writerow(headers)
#     for item in json_data:
#         csv_writer.writerow(item.values())

"""
Combine opentrolley data python code:
book_db = pd.read_csv("output.csv", engine="python")
print(book_db.head())

"""

lazada_db = pd.read_csv("output.csv")

with open("insert_sql_v3.py", "w") as f:
    f.write("session.add_all([")
    for index, row in lazada_db.iterrows():
        isbn = row["original_isbn"]
        price = row["price"]
        img = row["img"]
        url = row["url"]
        provider = row["provider"]
        values = f'LazadaBook("{isbn}", {price}, "{img}", "{url}", "{provider}"),\n'
        f.write(values)
    f.write("])")
