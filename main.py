import os
import sys
import asyncio
from telethon import TelegramClient, events
from fastapi import FastAPI
import uvicorn

# --- Environment variables ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "").strip()
PORT = int(os.getenv("PORT", 8000))

# --- Validate required env vars ---
missing = []
if not API_ID:
    missing.append("API_ID")
if not API_HASH:
    missing.append("API_HASH")
if not SESSION_NAME:
    missing.append("SESSION_NAME")

if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

API_ID = int(API_ID)

# --- Allowed users set ---
ALLOWED_USERS = set()
if ALLOWED_USERS_RAW:
    ALLOWED_USERS = {int(uid.strip()) for uid in ALLOWED_USERS_RAW.split(",") if uid.strip().isdigit()}

# --- Absolute session path ---
SESSION_PATH = os.path.join(os.getcwd(), f"{SESSION_NAME}.session")
if not os.path.isfile(SESSION_PATH):
    print(f"❌ Session file not found: {SESSION_PATH}")
    sys.exit(1)

# --- Telegram client ---
client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# --- Config ---
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
    await client.connect()
    if not await client.is_user_authorized():
        print(
            f"❌ Session file is invalid or not authorized: {SESSION_PATH}. "
            f"Make sure it was generated with the same API_ID/API_HASH."
        )
        sys.exit(1)

    me = await client.get_me()
    if me is None:
        print(
            f"❌ Could not retrieve account info from session: {SESSION_PATH}. "
            f"Make sure the session is valid."
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
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
