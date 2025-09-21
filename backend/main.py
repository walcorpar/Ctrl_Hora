from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
from uuid import uuid4
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "ctrl_hora")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

app = FastAPI()

# Configuración de CORS
origins = [
    "https://ctrl-hora-frontend.onrender.com",
    "https://ctrl-hora-admin-frontend.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Models
class User(BaseModel):
    username: str
    full_name: str
    rut: str  # Campo para RUT
    email: str
    phone_number: str
    password: str
    is_admin: bool = False
    registration_token: str = None
    entry_date: datetime = None
    exit_date: datetime = None

class Record(BaseModel):
    entry_time: datetime = None
    exit_time: datetime = None
    gps_position: str
    token: str
    user_rut: str  # Usar RUT como identificador

# Helper to check if user exists by RUT
def get_user_by_rut(rut: str):
    return db.users.find_one({"rut": rut})

# Authentication helper
def get_current_user(token: str = Depends(oauth2_scheme)):
    user = db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# Admin authentication helper
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# Login endpoint (using RUT)
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_rut(form_data.username)  # Use RUT as username
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = str(uuid4())
    db.users.update_one({"_id": user["_id"]}, {"$set": {"token": token}})
    return {"access_token": token, "token_type": "bearer"}

# Endpoint to register entry (only one per session)
@app.post("/entry")
async def register_entry(gps_position: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Administrators cannot register entries")
    # Check if there's an active entry
    active_entry = db.records.find_one({"user_rut": current_user["rut"], "exit_time": None})
    if active_entry:
        raise HTTPException(status_code=400, detail="You already have an active entry")
    record = {
        "user_rut": current_user["rut"],
        "entry_time": datetime.utcnow(),
        "gps_position": gps_position,
        "token": current_user["token"]
    }
    result = db.records.insert_one(record)
    inserted_record = db.records.find_one({"_id": result.inserted_id})
    if inserted_record:
        inserted_record["_id"] = str(inserted_record["_id"])
    return {"message": "Entry registered", "record": inserted_record}

# Endpoint to register exit (only one per session)
@app.post("/exit")
async def register_exit(gps_position: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Administrators cannot register exits")
    active_record = db.records.find_one({"user_rut": current_user["rut"], "exit_time": None})
    if not active_record:
        raise HTTPException(status_code=400, detail="No active entry found")
    update = {"$set": {"exit_time": datetime.utcnow(), "gps_position_exit": gps_position}}
    db.records.update_one({"_id": active_record["_id"]}, update)
    return {"message": "Exit registered"}

# Endpoint to add user (for initial setup, no auth required)
@app.post("/add-user")
async def add_user(user: User):
    if get_user_by_rut(user.rut):
        raise HTTPException(status_code=400, detail="User already exists")
    user_data = user.dict()
    user_data["password"] = get_password_hash(user.password)
    user_data["registration_token"] = str(uuid4())  # Generate unique token
    db.users.insert_one(user_data)
    return {"message": "User added", "registration_token": user_data["registration_token"]}

# Admin endpoints
@app.get("/api/users", dependencies=[Depends(get_current_admin_user)])
async def get_all_users():
    users = list(db.users.find({}, {"password": 0, "token": 0}))
    for user in users:
        user["_id"] = str(user["_id"])
    return users

@app.post("/api/users", status_code=201)
async def create_user(user: User, admin: dict = Depends(get_current_admin_user)):
    if get_user_by_rut(user.rut):
        raise HTTPException(status_code=400, detail="User already exists")
    user_data = user.dict()
    user_data["password"] = get_password_hash(user.password)
    user_data["registration_token"] = str(uuid4())
    db.users.insert_one(user_data)
    return {"message": "User created successfully", "registration_token": user_data["registration_token"]}

@app.put("/api/users/{rut}", dependencies=[Depends(get_current_admin_user)])
async def update_user(rut: str, user_update: User):
    user = get_user_by_rut(rut)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    if update_data:
        db.users.update_one({"rut": rut}, {"$set": update_data})
    return {"message": "User updated successfully"}

@app.delete("/api/users/{rut}", dependencies=[Depends(get_current_admin_user)])
async def delete_user(rut: str):
    result = db.users.delete_one({"rut": rut})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)