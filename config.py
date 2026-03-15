 import os

class Config:
    API_ID = int(os.environ.get("API_ID", 12345)) 
    API_HASH = os.environ.get("API_HASH", "your_api_hash")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
    
    # MongoDB Link (Heroku Config Vars se aayega)
    MONGO_URL = os.environ.get("MONGO_URL", "")
    
    # Log Channel ID Jahan report aayegi
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100123456789))

    # Owner ID (Sirf aap commands use kar sako isliye)
    OWNER_ID = int(os.environ.get("OWNER_ID", 12345678))
    
