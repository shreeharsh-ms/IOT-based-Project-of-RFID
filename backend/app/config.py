import os
from dotenv import load_dotenv

load_dotenv()   # Loads .env into environment variables

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
