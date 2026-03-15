import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

batch_data = {}

def get_id(text):
    if "t.me/c/" in text:
        return int(text.split('/')[-1])
    try:
        # Link se ID nikalne ka desi jugad agar link poora ho
        if "/c/" in text:
            return int(text.split('/')[-2])
        return int(text)
    except: return None

@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    batch_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source Channel ki ID ya link bhejo.")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "cancel"]))
async def handle_steps(client, message):
    user_id = message.from_user.id
    if user_id not in batch_data: return

    step = batch_data[user_id].get("step")

    if step == 1:
        batch_data[user_id]["source"] = get_id(message.text)
        batch_data[user_id]["step"] = 2
        await message.reply_text("📤 **Step 2:** Destination Channel ID bhejo.")
    elif step == 2:
        batch_data[user_id]["dest"] = get_id(message.text)
        batch_data[user_id]["step"] = 3
        await message.reply_text("🔢 **Step 3:** Start Message ID/Link?")
    elif step == 3:
        batch_data[user_id]["start"] = get_id(message.text)
        batch_data[user_id]["step"] = 4
        await message.reply_text("🏁 **Step 4:** End Message ID/Link?")
    elif step == 4:
        end = get_id(message.text)
        data = batch_data[user_id]
        start = data["start"]
        source = data["source"]
        dest = data["dest"]
        
        del batch_data[user_id]
        status = await message.reply_text("⏳ Processing...")
        
        count = 0
        for msg_id in range(start, end + 1):
            try:
                # copy_message use karenge direct, ye zyada powerful hai
                await client.copy_message(
                    chat_id=dest,
                    from_chat_id=source,
                    message_id=msg_id
                )
                count += 1
                if count % 5 == 0:
                    await status.edit(f"🚀 `{count}` bhej diye...")
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"Skip {msg_id}: {e}")
                continue
        
        await status.edit(f"✅ Kaam khatam! Total `{count}` videos bheji gayi.")

app.run()
