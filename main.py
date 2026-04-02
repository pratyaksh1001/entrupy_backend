from asyncio import current_task
from urllib import request
import os
from fastapi import FastAPI,Request
import bcrypt
import datetime
import sqlite3 as sql
import cachetools
import jwt
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

connection=sql.connect("db.sqlite3")
cursor=connection.cursor()
SECRET_KEY = "pratyaksh"
app = FastAPI()
timed_cache=cachetools.TTLCache(maxsize=100,ttl=3600)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://entrupy-frontend.vercel.app"],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Hello World"
    }

@app.post("/register")
async def register(request: Request):
    data=await request.json()
    print(data)
    email=data["email"]
    password=data["password"]
    email=data["email"]
    password=data["password"]
    hashed_pass=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(16))
    user_name=data["name"]
    api_limit=100
    age=data["age"]
    cursor.execute("insert into user values(?,?,?,?,?,?)",(email,hashed_pass,user_name,age,datetime.datetime.now(),api_limit))
    connection.commit()
    return {"message":"User registered successfully"}


@app.post("/login")
async def login(request: Request):
    data=await request.json()
    print(data)
    email=data["email"]
    password=data["password"]
    cursor.execute("select * from user where email=?",(email,))
    result=cursor.fetchone()
    if result:
        hashed_pass=result[1]
        if bcrypt.checkpw(password.encode("utf-8"), hashed_pass):
            cursor.execute("insert into user_logs values(?,?,?)",(email,datetime.datetime.now(),0))
            connection.commit()
            print("login success")
            token = jwt.encode(
                {"email": email},
                SECRET_KEY,
                algorithm="HS256"
            )
            timed_cache[token] = {"email": email, "user_name": result[2],"remaining_tokens":result[-1]}

            return {
                "message": "Login Successful",
                "user_name": result[2],
                "success": True,
                "token": token
            }
        else:
            return {"message":"Wrong Password","success": False}
    else:
        return {"message":"User Not Found","success": False}

@app.post("/auth")
async def auth(request: Request):
    data=await request.json()
    token=data["token"]
    if token in timed_cache:
        cached_data=timed_cache[token]
        return {"success":True,"data":cached_data}
    else:
        return {"success":False}

@app.post("/product_list")
async def product_list(request: Request):
    data=await request.json()
    q=data["query"]
    token=data["token"]
    if token in timed_cache:
        if timed_cache[token]["remaining_tokens"]>0:
            cached_data=timed_cache[token]
            cursor.execute("insert into user_logs values(?,?,?)",(cached_data["email"],datetime.datetime.now(),2))
            timed_cache[token]["remaining_tokens"]-=2
            cursor.execute(f"select * from product where product like '%{q}%' ")
            data=cursor.fetchall()
            products=[]
            for product in data:
                d={}
                d["pID"]=product[0]
                d["product"]=product[1]
                d["price"]=product[2]
                d["category"]=product[-2]
                d["brand"]=product[-3]
                d["url"]=product[-1]
                products.append(d)
            return {"success":True,"data":products}
        else:
            return {"success":False}

@app.post("/product/{pID}")
async def get_product(request: Request, pID: str):

    data=await request.json()
    token=data["token"]
    if timed_cache[token]["remaining_tokens"]>0:
        timed_cache[token]["remaining_tokens"]-=5
    else:
        return {"success":False,"error":"tokens exhausted, kindly wait"}

    cursor.execute("select * from product where pID=?",(pID,))
    result=cursor.fetchone()
    cursor.execute(
        "select * from prod_price where pID=? order by updated_at",(pID,))
    history=cursor.fetchall()
    print(history)
    cursor.execute("select * from prod_img where pID=?",(pID,))
    images=cursor.fetchall()
    images=[image for _,image in images]
    prices=[i[1] for i in history]
    time_stamps=[i[2] for i in history]
    product={}
    product["pID"]=pID
    product["product"]=result[1]
    product["price"]=result[2]
    product["category"]=result[-2]
    product["brand"]=result[-3]
    data=[]
    for i in range(len(history)):
        data.append({time_stamps[i]:prices[i]})
    print(history)
    print(images)
    return {"success":True,"images":images,"product":product,"data":data}



@app.post("/admin_login")
async def admin_login(request: Request):
    data = await request.json()
    print(data)
    email = data["email"]
    password = data["password"]
    cursor.execute("select * from admin where email=?", (email,))
    result = cursor.fetchone()
    if result:
        hashed_pass = result[1]
        if bcrypt.checkpw(password.encode("utf-8"), hashed_pass):
            print("login success")
            token = jwt.encode(
                {"email": email},
                SECRET_KEY,
                algorithm="HS256"
            )
            timed_cache[token] = {"email": email, "user_name": result[2],"role":"admin"}

            return {
                "message": "Login Successful",
                "user_name": result[2],
                "success": True,
                "token": token
            }
        else:
            return {"message": "Wrong Password", "success": False}
    else:
        return {"message": "User Not Found", "success": False}

@app.post("/admin_auth")
async def admin_auth(request: Request):
    data=await request.json()
    token=data["token"]
    if token in timed_cache:
        cached_data=timed_cache[token]
        if cached_data["role"]=="admin":
            return {"success":True}
    else:
        return {"success":False}


@app.get("/tables")
def get_tables(request: Request):

    table_names=["prod_price","product","user","prod_img"]
    return {"success":True,"tables":table_names}


@app.post("/{table}")
async def return_table(request: Request, table: str):
    data=await request.json()
    token=data["token"]
    print(table)
    email=timed_cache[token]["email"]
    print(email)
    cursor.execute(f"select * from {table}")
    columns=cursor.description
    columns=[i[0] for i in columns]
    print(columns)
    rows=cursor.fetchmany(10)
    print(rows)
    return {"success":True,"data":rows,"columns":columns}

@app.post("/admin/search")
async def admin_search(request: Request):
    data=await request.json()
    print(data)
    token=data["token"]
    query=data["query"]
    column=data["column"]
    table=data["table"]
    cursor.execute(f"select * from {table} where {column} like '%{query}%'")
    result=cursor.fetchall()
    des=cursor.description
    columns=[column[0] for column in des]
    print(result)
    return {"success":True,"data":result,"columns":columns}

@app.post("/admin/update")
async def admin_modification(request: Request):
    data=await request.json()
    print(data)
    token=data["token"]
    column = data["column"]
    table = data["table"]
    updated_val=data["value"]
    pID=data["pID"]
    if timed_cache[token]["role"]=="admin":
        cursor.execute(
            f"UPDATE {table} SET {column}=? WHERE pID=?",
            (updated_val, pID)
        )
        if column=="price":
            cursor.execute("insert into prod_price values(?,?,?,?)",(pID,updated_val,datetime.datetime.now(),timed_cache[token]["email"]))
        connection.commit()
        return {"success":True,"data":updated_val,"pID":pID}
    return {"success":False}