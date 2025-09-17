from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware  # Importa el middleware de CORS
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

# -----------------
# Configuración de CORS
# -----------------
origins = [
    "https://ctrl-hora-frontend.onrender.com",  # La URL exacta de tu frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)
# -----------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Models
class User(BaseModel):
    username: str
    password: str
    is_admin: bool = False  # Default to False

class Record(BaseModel):
    entry_time: datetime = None
    exit_time: datetime = None
    gps_position: str
    token: str
    user_id: str

# Helper to check if user exists
def get_user(username: str):
    return db.users.find_one({"username": username})

# Helper to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Login endpoint
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = str(uuid4())
    db.users.update_one({"_id": user["_id"]}, {"$set": {"token": token}})
    return {"access_token": token, "token_type": "bearer"}

# Endpoint to register entry
@app.post("/entry")
async def register_entry(gps_position: str, token: str = Depends(oauth2_scheme)):
    user = db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    record = {
        "user_id": user["username"],
        "entry_time": datetime.utcnow(),
        "gps_position": gps_position,
        "token": token
    }
    
    result = db.records.insert_one(record)
    
    # ----------------------------------------------------
    #  SOLUCIÓN: CONVERTIR EL _id A STRING PARA EVITAR ERRORES
    # ----------------------------------------------------
    # Obtener el documento insertado y convertir el _id
    inserted_record = db.records.find_one({"_id": result.inserted_id})
    if inserted_record:
        inserted_record["_id"] = str(inserted_record["_id"])
    
    return {"message": "Entry registered", "record": inserted_record}


# Endpoint to register exit
@app.post("/exit")
async def register_exit(gps_position: str, token: str = Depends(oauth2_scheme)):
    user = db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    latest_record = db.records.find_one({"user_id": user["username"], "exit_time": None}, sort=[("entry_time", -1)])
    if not latest_record:
        raise HTTPException(status_code=400, detail="No active entry found")
    update = {"$set": {"exit_time": datetime.utcnow(), "gps_position_exit": gps_position}}
    db.records.update_one({"_id": latest_record["_id"]}, update)
    return {"message": "Exit registered"}

# Add user
@app.post("/add-user")
async def add_user(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="User already exists")
    user_data = user.dict()
    user_data["password"] = get_password_hash(user.password)
    db.users.insert_one(user_data)
    return {"message": "User added"}

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# -------------------- MÓDULO DE ADMINISTRACIÓN DE USUARIOS --------------------

@app.get("/api/users", dependencies=[Depends(get_current_admin_user)])
async def get_all_users():
    # Obtiene todos los usuarios y excluye la contraseña por seguridad
    users = list(db.users.find({}, {"password": 0, "token": 0}))
    for user in users:
        user["_id"] = str(user["_id"])
    return users

@app.post("/api/users", status_code=201)
async def create_user(user: User, admin: dict = Depends(get_current_admin_user)):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="User already exists")
    db.users.insert_one(user.dict())
    return {"message": "User created successfully"}

@app.put("/api/users/{username}", dependencies=[Depends(get_current_admin_user)])
async def update_user(username: str, user_update: User):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Actualizar solo los campos proporcionados
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        db.users.update_one({"username": username}, {"$set": update_data})
    
    return {"message": "User updated successfully"}

@app.delete("/api/users/{username}", dependencies=[Depends(get_current_admin_user)])
async def delete_user(username: str):
    result = db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)