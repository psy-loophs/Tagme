import os
import sys
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from fastapi import FastAPI
import uvicorn
import threading

# --- Environment variables ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "").strip()

# --- Validate required env vars ---
missing = []
if not API_ID:
    missing.append("API_ID")
if not API_HASH:
    missing.append("API_HASH")
if not SESSION_STRING:
    missing.append("SESSION_STRING")

if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

API_ID = int(API_ID)

# --- Allowed users set ---
ALLOWED_USERS = set()
if ALLOWED_USERS_RAW:
    ALLOWED_USERS = {int(uid.strip()) for uid in ALLOWED_USERS_RAW.split(",") if uid.strip().isdigit()}

# --- Telegram client using string session ---
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

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
@client.on(events.NewMessage(pattern=f"^{TRIGGER_TAG}(.*)", regex_flags=re.DOTALL))
# @client.on(events.NewMessage(pattern=f"^{TRIGGER_TAG}(.*)"))
async def mention_all(event):
    global OWNER_ID
    sender_id = event.sender_id  # ✅ safe: always available
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
    sender_id = event.sender_id  # ✅ safe fix
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
        print("❌ Session is invalid or expired. Make sure SESSION_STRING is correct.")
        sys.exit(1)

    me = await client.get_me()
    if me is None:
        print("❌ Could not retrieve account info. SESSION_STRING may be invalid.")
        sys.exit(1)
    OWNER_ID = me.id
    print(f"👑 Owner ID detected: {OWNER_ID}")

# --- FastAPI health server ---
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "Userbot is alive"}

def run_health_server():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# --- Run bot ---
async def main():
    await init_owner()
    print("🚀 Userbot is running...")

    # Start FastAPI server in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
