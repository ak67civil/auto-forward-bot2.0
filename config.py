import os

class Config:
    API_ID = int(os.environ.get("API_ID", 12345)) 
    API_HASH = os.environ.get("API_HASH", "your_api_hash")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
    
    # List IDs separated by space in Heroku, then split here
    FROM_CHANNELS = [int(x) if x.startswith("-100") else x for x in os.environ.get("FROM_CHANNELS", "-100123 -100456").split()]
    TO_CHANNEL = int(os.environ.get("TO_CHANNEL", -100987654321))
    
