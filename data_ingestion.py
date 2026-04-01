import sqlite3 as sql
import json
import datetime
connection=sql.connect("db.sqlite3")

cursor=connection.cursor()

cursor.execute('create table if not exists product(pID text primary key, product text,price float, last_updated timestamp, brand text,category text)')
cursor.execute("create table if not exists prod_img(pID text,url text)")
cursor.execute("create table if not exists user(email text primary key,password text,user_name text,age int,user_created_at timestamp,request_limit int)")
cursor.execute("create table if not exists user_logs(email text,logged_in_at timestamp,requests_hit int)")
connection.commit()

for i in range(1,31):
    if i<10:
        i="0"+str(i)
    else:
        i=str(i)
    with open(f"sample_products/1stdibs_chanel_belts_{i}.json") as f:
        data=json.load(f)
        url=data["product_url"]
        price=data["price"]
        brand=data["brand"]
        pID=data["product_id"]
        prod=data["model"]
        category="belts"
        cursor.execute("insert into product values(?,?,?,?,?,?)",(pID,prod,price,datetime.datetime.now(),brand,category))
        images = data["main_images"]
        for image in images:
            cursor.execute("insert into prod_img values(?,?)", (pID, image["url"]))

for i in range(1,31):
    if i<10:
        i="0"+str(i)
    else:
        i=str(i)
    with open(f"sample_products/fashionphile_tiffany_{i}.json") as f:
        data=json.load(f)
        price=data["price"]
        brand=data["brand"]
        prod=data["model"]
        pID=data["product_id"]
        url=data["image_url"]
        category=data["metadata"]["garment_type"]
        cursor.execute("insert into product values(?,?,?,?,?,?)",(pID,prod,price,datetime.datetime.now(),brand,category))

        images = data["main_images"]
        for image in images:
            cursor.execute("insert into prod_img values(?,?)", (pID, image["url"]))

for i in range(1,31):
    if i < 10:
        i = "0" + str(i)
    else:
        i = str(i)
    with open(f"sample_products/grailed_amiri_apparel_{i}.json") as f:
        data = json.load(f)
        price = data["price"]
        brand = data["brand"]
        prod = data["model"]
        pID = data["product_id"]
        url = data["image_url"]
        category = data["metadata"]["style"]
        cursor.execute("insert into product values(?,?,?,?,?,?)", (pID, prod, price, datetime.datetime.now(), brand,category))

        images = data["main_images"]
        for image in images:
            cursor.execute("insert into prod_img values(?,?)", (pID, image["url"]))

connection.commit()