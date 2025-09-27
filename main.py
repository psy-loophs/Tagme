import os
from fastapi import FastAPI
import asyncio
from telethon import TelegramClient, events
import uvicorn
import sys

# --- Environment variables ---
api_id = int(os.getenv("API_ID", 0))
api_hash = os.getenv("API_HASH", "")
session_name = os.getenv("SESSION_NAME", "userbot")
allowed_users_raw = os.getenv("ALLOWED_USERS", "").strip()

if not api_id or not api_hash:
    print("❌ API_ID and API_HASH must be set in environment variables.")
    sys.exit(1)

# --- Allowed users ---
ALLOWED_USERS = set()
if allowed_users_raw:
    ALLOWED_USERS = {int(uid.strip()) for uid in allowed_users_raw.split(",") if uid.strip().isdigit()}

# --- Telegram client ---
client = TelegramClient(session_name, api_id, api_hash)

# === Config ===
TRIGGER_TAG = "!tagall"
TRIGGER_STOP = "!stop"
tagging_active = {}
OWNER_ID = None

# --- Authorization helper ---
async def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return user_id == OWNER_ID
    return user_id == OWNER_ID or user_id in ALLOWED_USERS

# --- Event handlers ---
@client.on(events.NewMessage(pattern=f"^{TRIGGER_TAG}(.*)"))
async def mention_all(event):
    global OWNER_ID
    sender = await event.get_sender()
    sender_id = sender.id
    if not await is_authorized(sender_id):
        return

    chat_id = event.chat_id
    custom_text = event.pattern_match.group(1).strip()
    if not event.is_group:
        await event.reply("❌ This command only works in groups.")
        return
    if tagging_active.get(chat_id, False):
        await event.reply("⚠ Tagging is already running. Use !stop to cancel.")
        return

    try:
        tagging_active[chat_id] = True
        await event.reply("🔍 Fetching members...")
        participants = await client.get_participants(chat_id)
        if not participants:
            await event.reply("❌ No members found.")
            tagging_active[chat_id] = False
            return

        await event.reply(f"🚀 Tagging {len(participants)} members...")
        reply_to = event.reply_to_msg_id if event.is_reply else None

        for user in participants:
            if not tagging_active.get(chat_id):
                await event.reply("🛑 Tagging stopped.")
                break
            if user.bot:
                continue
            name = user.first_name or "User"
            mention = f"[{name}](tg://user?id={user.id})"
            message = mention + (f" {custom_text}" if custom_text else "")
            try:
                await client.send_message(chat_id, message, reply_to=reply_to)
            except Exception as e:
                await event.reply(f"⚠ Error: {e}")
                break

        if tagging_active.get(chat_id):
            await event.reply("✅ Done tagging everyone.")
        tagging_active[chat_id] = False

    except Exception as e:
        await event.reply(f"❌ Error: `{e}`")
        tagging_active[chat_id] = False

@client.on(events.NewMessage(pattern=TRIGGER_STOP))
async def stop_tagging(event):
    global OWNER_ID
    sender = await event.get_sender()
    sender_id = sender.id
    if not await is_authorized(sender_id):
        return
    chat_id = event.chat_id
    if tagging_active.get(chat_id):
        tagging_active[chat_id] = False
        await event.reply("🛑 Tagging stopped.")
    else:
        await event.reply("⚠ No tagging in progress.")

# --- Initialize owner ---
async def init_owner():
    global OWNER_ID
    await client.connect()  # Headless-safe
    me = await client.get_me()
    if me is None:
        print(
            "❌ Could not retrieve account info. Make sure the .session file exists and SESSION_NAME is correct."
        )
        sys.exit(1)
    OWNER_ID = me.id
    print(f"👑 Owner ID detected: {OWNER_ID}")

# --- FastAPI web server for uptime monitoring ---
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Userbot is running 🚀"}

# --- Run bot and web server ---
async def main():
    await init_owner()
    print("🚀 Userbot is running...")
    # Start Telegram client in background
    asyncio.create_task(client.run_until_disconnected())
    # Start FastAPI server
    port = int(os.getenv("PORT", 8000))
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
