from pymongo import MongoClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "ctrl_hora")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Migrar contraseñas
users = db.users.find()
for user in users:
    plain_password = user["password"]
    hashed_password = get_password_hash(plain_password)
    db.users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_password}})
    print(f"Updated password for {user['username']}")

print("Migration completed.")