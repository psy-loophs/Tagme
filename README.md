# Telegram TagAll Bot (Telethon)

A simple Telegram bot built with **Telethon** that can tag all users in a group.  
Includes owner-only and allowed-users access control, and stop/start tagging support.  

---

## ✨ Features
- `/tagall` → Mentions all group members.  
- Prevents multiple tagging sessions at once.  
- `!stop` → Stops tagging process.  
- Access control:
  - If `ALLOWED_USERS` is empty → only the **API owner** can use the bot.
  - If `ALLOWED_USERS` is set → both the API owner and listed users can use it.

---

## ⚡ Setup

### 1. Get Telegram API credentials
1. Go to [my.telegram.org](https://my.telegram.org).  
2. Log in with your Telegram number.  
3. Create a new app → copy your **API ID** and **API Hash**.

---

### 2. Generate Session File
You need a Telegram session file (`mention_bot.session`) before deployment.

Create a file called `generate_session.py` with this code:

```python
from telethon import TelegramClient

api_id = int(input("Enter your API_ID: "))
api_hash = input("Enter your API_HASH: ")
session_name = input("Enter your session name: ")

client = TelegramClient(session_name, api_id, api_hash)

async def main():
    await client.start()
    print(f"✅ Session file generated: {session_name}.session")

with client:
    client.loop.run_until_complete(main()) ```

> 📝 When you run this script, you will be asked to:
> - **API_ID** → The numeric ID from [my.telegram.org](https://my.telegram.org).  
> - **API_HASH** → The secret hash from the same place.  
> - **Session name** → Any name you like (e.g., `mention_bot`).  
>
> The session name determines the filename of your session (e.g., entering `mention_bot` creates `mention_bot.session`).  
> You can create multiple sessions with different names if needed.  
>
> ⚡ Important: You must always provide your own **API ID**, **API Hash**, and a **session name** whenever you run this code (locally or on a server).
