import os

class Config:
    API_ID = int(os.environ.get("API_ID", 12345))
    API_HASH = os.environ.get("API_HASH", "your_hash")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
    MONGO_URL = os.environ.get("MONGO_URL", "")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100123456789))
    OWNER_ID = int(os.environ.get("OWNER_ID", 12345678))
 
    
