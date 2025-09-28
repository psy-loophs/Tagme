# Telegram TagAll Bot (Telethon)

A simple Telegram user bot built with **Telethon** that can tag all users in a group.  
Includes owner-only and allowed-users access control, and stop/start tagging support.  

---

## ✨ Usage
- `/tagall` → Mentions all group members.  
- Prevents multiple tagging sessions at once.  
- `!stop` → Stops tagging process.  
- Access control:
  - If `ALLOWED_USERS` is empty → only the **API owner** can use the bot.
  - If `ALLOWED_USERS` is set → both the API owner and listed users can use it.
 
  ---

  ## Features

- First name mentions: 
  - Instead of showing full usernames, the bot tag members using their first names only, making the chat cleaner.

- Custom messages:
  - Use !tagall &lt;message&gt; to mention all members along with your custom message.

Works whether you reply to a message or not.


- Reply tagging:
  - If you reply to any message with !tagall, the bot will tag all members in reply to that message.


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
from telethon.sessions import StringSession

api_id = int(input("Enter your API_ID: "))
api_hash = input("Enter your API_HASH: ")
session_name = input("Enter your session name: ")

client = TelegramClient(StringSession(), api_id, api_hash)

async def main():
    await client.start()

    # Save session string to file as text
    with open(f"{session_name}.session", "w") as f:
        f.write(client.session.save())

    print(f"✅ Session file generated: {session_name}.session")
    print(f"💡 Session string:\n{client.session.save()}")

with client:
    client.loop.run_until_complete(main())
```


📝 When you run this script, you will be asked to:

⦁ API_ID → The numeric ID from my.telegram.org.

⦁ API_HASH → The secret hash from the same place.

⦁ Session name → Any name you like (e.g., mention_bot).


⚡ During the first login, you will also provide:

⦁ Phone number → Your Telegram account number.

⦁ OTP → One-time password sent via SMS or Telegram app.

⦁ 2FA password → If two-factor authentication is enabled.


✅ After successful login, this script generates a session string, which is a critical piece for headless deployments:

You must store this session string in your .env file (as SESSION_STRING) or as an environment variable.

Using the session string allows the bot to run without re-entering your phone number, OTP, or 2FA.

Keep the session string private — anyone with it can access your Telegram account.


⚡ Important: To run this bot, you must provide your own API ID, API Hash, and SESSION_STRING. Once stored, the bot can start automatically without further manual login.




---
