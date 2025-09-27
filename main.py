import os
from telethon import TelegramClient, events

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")

client = TelegramClient(session_name, api_id, api_hash)
# Parse allowed users
allowed_users_raw = os.getenv("ALLOWED_USERS", "").strip()
ALLOWED_USERS = set()
if allowed_users_raw:
    ALLOWED_USERS = {int(uid.strip()) for uid in allowed_users_raw.split(",") if uid.strip().isdigit()}

client = TelegramClient(session_name, api_id, api_hash)

# === Config ===
TRIGGER_TAG = "!tagall"
TRIGGER_STOP = "!stop"

# Track tagging state per chat
tagging_active = {}

# Will store owner id after startup
OWNER_ID = None


async def is_authorized(user_id: int) -> bool:
    """Check if user is allowed to run commands."""
    if not ALLOWED_USERS:
        # Only the owner can use commands when empty
        return user_id == OWNER_ID
    else:
        # Owner + allowed users
        return user_id == OWNER_ID or user_id in ALLOWED_USERS


@client.on(events.NewMessage(pattern=f"^{TRIGGER_TAG}(.*)"))
async def mention_all(event):
    global OWNER_ID
    sender = await event.get_sender()
    sender_id = sender.id

    if not await is_authorized(sender_id):
        return  # ❌ Unauthorized → do nothing

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

        # Decide reply target (original replied msg OR None)
        reply_to = event.reply_to_msg_id if event.is_reply else None

        for user in participants:
            if not tagging_active.get(chat_id):
                await event.reply("🛑 Tagging stopped.")
                break

            if user.bot:
                continue

            name = user.first_name or "User"
            mention = f"[{name}](tg://user?id={user.id})"

            message = f"{mention}"
            if custom_text:
                message += f" {custom_text}"

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
        return  # ❌ Unauthorized → do nothing

    chat_id = event.chat_id
    if tagging_active.get(chat_id):
        tagging_active[chat_id] = False
        await event.reply("🛑 Tagging stopped.")
    else:
        await event.reply("⚠ No tagging in progress.")


async def init_owner():
    """Get and set owner id (the account running this userbot)."""
    global OWNER_ID
    me = await client.get_me()
    OWNER_ID = me.id
    print(f"👑 Owner ID detected: {OWNER_ID}")


print("🚀 Userbot is running...")
client.start()
client.loop.run_until_complete(init_owner())
client.run_until_disconnected()
