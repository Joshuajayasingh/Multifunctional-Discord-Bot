
# Discord Assistant Bot

A full-featured Discord bot that brings AI, music, media downloading, and utility tools directly to your server — powered by Gemini, GPT, YouTube, and Discord slash commands.

---

## DISCLAIMER

This bot is provided **as-is for educational or personal use**.  
**Use at your own risk.** Downloading media from YouTube or using AI services may violate respective terms of service.  
The author is **not responsible** for account bans, misuse, or violations of any service's policies.

---

## Features

### Music Playback
- `/play <query>` — Play songs from YouTube
  ![WhatsApp Image 2025-06-18 at 03 18 53_5dd2ff1a](https://github.com/user-attachments/assets/1b957178-8b65-4b63-97c3-32020006c221)
  ![WhatsApp Image 2025-06-18 at 03 19 05_878a9b15](https://github.com/user-attachments/assets/9a42a2d7-5ca0-41a6-932c-345337ec8f98)

- `/queue` — Show the song queue
  ![WhatsApp Image 2025-06-18 at 03 20 44_fac6b68d](https://github.com/user-attachments/assets/57c6653d-164f-4f50-8a3e-5b0629286bf4)
- `/pause`, `/resume`, `/stop`, `/skip`, `/leave`
  ![WhatsApp Image 2025-06-18 at 03 22 22_1a3d32c0](https://github.com/user-attachments/assets/112ef69d-6770-4e10-8e9e-903268176ae8)
  ![WhatsApp Image 2025-06-18 at 03 22 44_f9c9ade3](https://github.com/user-attachments/assets/ee9af237-c707-4939-8d3c-dc114ac4edc0)
  ![WhatsApp Image 2025-06-18 at 03 23 00_e4d1e84c](https://github.com/user-attachments/assets/930021e4-246e-4726-a20e-fed368478788)
  ![WhatsApp Image 2025-06-18 at 03 23 41_dc10f3fc](https://github.com/user-attachments/assets/be853704-2cb2-4063-995c-e2e953b6bcf0)
  ![image](https://github.com/user-attachments/assets/9ba529b0-16a3-4208-adfc-ee02053bac1d)

- `/removelastsong` — Remove the most recent track
  ![WhatsApp Image 2025-06-18 at 03 21 39_b0f49bdf](https://github.com/user-attachments/assets/7868a674-4a6e-4791-b3e6-044f8f1ec0c8)

### Media Downloader
- `/mp3 <YouTube URL>` — Download MP3 files from YouTube
  ![image](https://github.com/user-attachments/assets/28181f03-c174-4450-ab6d-0e0cb1ff93c7)
- `/mp4 <YouTube URL>` — Download MP4 files from YouTube
  ![image](https://github.com/user-attachments/assets/e5b862b1-3b21-46bc-afc6-e9a17526d64f)
- Smart file size handling to respect Discord limits

### AI Chat
- `/gemini <prompt>` — Ask **Google Gemini**
  ![WhatsApp Image 2025-06-18 at 03 10 47_95e91276](https://github.com/user-attachments/assets/9b9e4a9e-1507-445a-9d65-14849ed2dd1a)
- `/gpt <prompt>` — Ask **OpenAI ChatGPT**
  ![WhatsApp Image 2025-06-18 at 03 11 39_34cc8414](https://github.com/user-attachments/assets/117cfda4-57c7-47d2-aa28-ce22304ba924)

### Utilities
- `/timer <seconds> <label>` — Countdown timer
  ![image](https://github.com/user-attachments/assets/77af3b76-3191-49c7-8365-5d21f20465a8)
- `/stopwatch <start|stop>` — Stopwatch tool
  ![image](https://github.com/user-attachments/assets/032b14b1-14f9-4a13-8f2c-5cd62f467ed0)
- `/alarm <hour> <minute> <label>` — Daily Alarm
  ![image](https://github.com/user-attachments/assets/d2e71864-d6e3-4073-beda-d42aaa6c3f70)
  
### Help
- `/help` — Lists all available commands and usage
  ![WhatsApp Image 2025-06-18 at 13 23 12_f719768e](https://github.com/user-attachments/assets/213316c8-378f-4add-94f8-9ff059c5a704)
  ![WhatsApp Image 2025-06-18 at 03 17 07_401669dc](https://github.com/user-attachments/assets/241909d2-7df0-425b-b3a6-e6973479ef7e)

---

## Requirements

- Python 3.9+
- Discord bot token
- Valid Gemini & GPT API keys (optional but recommended)

Install dependencies:

```bash
pip install discord yt_dlp aiohttp openai google-generativeai nest_asyncio
````

---

## Configuration

Edit the following lines in `discordbot.py`:

```python
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
gpt_client = OpenAI(
    base_url="YOUR_GPT_API_BASE_URL_HERE",
    api_key="YOUR_GPT_API_KEY_HERE"
)
```

Optional:

* Set download path: `DOWNLOAD_DIR = "downloads"`
* You can modify `MAX_FILE_SIZE` to limit media uploads

---

## How to Run

```bash
python discordbot.py
```

Ensure the bot has:

* "Message Content Intent" enabled in the Discord Developer Portal
* Proper permissions (Administrator recommended for testing)

---

## Notes

* Music playback uses `yt_dlp` and `FFmpeg`
* File uploads are limited to <25MB due to Discord file size restrictions
* Uses slash commands via `discord.app_commands` (no `!` prefix needed)

---

##  Security

* NEVER commit or share your bot token or API keys.

---

## Example Commands

```text
/play never gonna give you up
/mp3 https://www.youtube.com/watch?v=dQw4w9WgXcQ
/gpt Write a short story on the rise of AI
/gemini Explain quantum physics in simple terms
/timer 60 Time’s up!
```

---

## License

This project is open for educational and non-commercial use.
Not affiliated with Discord, Google, YouTube, or OpenAI.


