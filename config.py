import os

class Config:
    # Telegram API Credentials
    API_ID = int(os.environ.get("API_ID", 1234567)) # Apna API ID yahan likhein ya Environment Variable set karein
    API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token_here")

    # Forwarding Settings
    # Source Channels: Jahan se message uthana hai (IDs ya Usernames ki list)
    FROM_CHANNELS = [-100123456789, "source_channel_username"]
    
    # Destination Channel: Jahan forward karna hai
    TO_CHANNEL = -100987654321

    # Optional: Agar message se purane channel ka link/naam hatana ho
    REMOVE_CAPTION = True
