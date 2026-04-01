from fastapi import FastAPI,Request
import bcrypt
import datetime
import sqlite3 as sql
import cachetools
import jwt

connection=sql.connect("db.sqlite3")
cursor=connection.cursor()

app = FastAPI()
timed_cache=cachetools.TTLCache(ttl=3600)

@app.get("/")
async def root():
    return {
        "message": "Hello World"
    }

@app.post("/register")
async def register(request: Request):
    data=await request.json()
    email=data["email"]
    password=data["password"]
    hashed_pass=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(16))
    user_name=data["user_name"]
    api_limit=100
    age=data["age"]
    cursor.execute("insert into users values(?,?,?,?,?)",(email,hashed_pass,user_name,api_limit,age,datetime.datetime.now()))
    connection.commit()
    return {"message":"User registered successfully"}

@app.post("/login")
async def login(request: Request):
    data=await request.json()
    email=data["email"]
    password=data["password"]
    cursor.execute("select * from user where email=?",(email,))
    result=cursor.fetchone()
    if result:
        hashed_pass=result[1]
        if bcrypt.checkpw(password.encode("utf-8"), hashed_pass):
            token=jwt.encode(payload={"email":email,},secret=password.encode("utf-8"),algorithm="HS256")
            timed_cache[token]={"email":email,"user_name":result[2]}
            cursor.execute("insert into user_logs values(?,?,?",(email,datetime.datetime.now(),0))
            return {"message":"Login Successful","user_name":result[2],"success": True}
        else:
            return {"message":"Wrong Password","success": False}
    else:
        return {"message":"User Not Found","success": False}

@app.get("/auth")
async def auth(request: Request):
    data=await request.json()
    token=data["token"]
    if token in timed_cache:
        cached_data=timed_cache[token]
        return {"success":True,"data":cached_data}
    else:
        return {"success":False}
