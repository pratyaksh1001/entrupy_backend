from fastapi import FastAPI,Request
import bcrypt
import datetime
import sqlite3 as sql
import cachetools
import jwt
from fastapi.middleware.cors import CORSMiddleware

connection=sql.connect("db.sqlite3")
cursor=connection.cursor()
SECRET_KEY = "pratyaksh"
app = FastAPI()
timed_cache=cachetools.TTLCache(maxsize=100,ttl=3600)

# Wildcard "*" cannot be used with allow_credentials=True (browser CORS rules).
# Regex matches any Origin so each request gets a reflected Access-Control-Allow-Origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","http://localhost:3000"],
    allow_credentials=True,
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

@app.get("/product/{pID}")
async def get_product(request: Request, pID: str):
    cursor.execute("select * from product where pID=?",(pID,))
    result=cursor.fetchone()
    cursor.execute("select * from prod_price where pID=? order by updated_at",(pID,))
    history=cursor.fetchall()
    cursor.execute("select * from prod_img where pID=?",(pID,))
    images=cursor.fetchall()
    images=[image for _,image in images]
    history=[i[1] for i in history]
    print(history)
    print(images)
    return {"success":True,"images":images,"history":history}