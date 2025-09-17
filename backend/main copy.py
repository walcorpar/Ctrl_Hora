from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
from uuid import uuid4
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "ctrl_hora"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Models
class User(BaseModel):
    username: str
    password: str  # In production, hash this!

class Record(BaseModel):
    entry_time: datetime = None
    exit_time: datetime = None
    gps_position: str  # e.g., "lat,long"
    token: str
    user_id: str

# Helper to check if user exists
def get_user(username: str):
    return db.users.find_one({"username": username})

# Login endpoint
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or user["password"] != form_data.password:  # In prod, use hashed comparison
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = str(uuid4())  # Unique token
    return {"access_token": token, "token_type": "bearer"}

# Endpoint to register entry
@app.post("/entry")
async def register_entry(gps_position: str, token: str = Depends(oauth2_scheme)):
    user = db.users.find_one({"token": token})  # Validate token (in prod, use JWT)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    record = {
        "user_id": user["username"],
        "entry_time": datetime.utcnow(),
        "gps_position": gps_position,
        "token": token
    }
    db.records.insert_one(record)
    return {"message": "Entry registered", "record": record}

# Endpoint to register exit
@app.post("/exit")
async def register_exit(gps_position: str, token: str = Depends(oauth2_scheme)):
    user = db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Find the latest entry without exit
    latest_record = db.records.find_one({"user_id": user["username"], "exit_time": None}, sort=[("entry_time", -1)])
    if not latest_record:
        raise HTTPException(status_code=400, detail="No active entry found")
    update = {"$set": {"exit_time": datetime.utcnow(), "gps_position_exit": gps_position}}
    db.records.update_one({"_id": latest_record["_id"]}, update)
    return {"message": "Exit registered"}

# For demo: Add a user (in prod, use registration endpoint with hashing)
@app.post("/add-user")
async def add_user(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="User exists")
    db.users.insert_one(user.dict())
    return {"message": "User added"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)