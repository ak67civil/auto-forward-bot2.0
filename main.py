from pyrogram import Client, filters
from config import Config

app = Client(
    "forwarder_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.chat(Config.FROM_CHANNELS))
async def forward_handler(client, message):
    try:
        # Message ko target channel par copy karna
        await message.copy(chat_id=Config.TO_CHANNEL)
        print(f"Success: Forwarded message {message.id}")
    except Exception as e:
        print(f"Error occurred: {e}")

print("Bot is running...")
app.run()
