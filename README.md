
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
- `/pause`, `/resume`, `/stop`, `/skip`, `/leave`
- `/queue` — Show the song queue
- `/removelastsong` — Remove the most recent track

### Media Downloader
- `/mp3 <YouTube URL>` — Download and upload MP3
- `/mp4 <YouTube URL>` — Download and upload MP4
- Smart file size handling to respect Discord limits

### AI Chat
- `/gemini <prompt>` — Ask **Google Gemini**
- `/gpt <prompt>` — Ask **OpenAI GPT-4 or similar**

### Utilities
- `/timer <seconds> <label>` — Countdown timer
- `/stopwatch <start|stop|reset>` — Stopwatch tool
- `/alarm <hour> <minute> <label>` — Daily alarm

### Help
- `/help` — Lists all available commands and usage

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
/gpt Write a short poem about AI
/gemini Explain quantum physics in simple terms
/timer 60 Time’s up!
```

---

## License

This project is open for educational and non-commercial use.
Not affiliated with Discord, Google, YouTube, or OpenAI.


