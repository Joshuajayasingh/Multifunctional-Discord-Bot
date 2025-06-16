import os
import uuid
import aiohttp
import yt_dlp
import discord
import asyncio
import datetime
import google.generativeai as genai
import random
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from openai import OpenAI
import json
import mimetypes
import tempfile
import nest_asyncio
nest_asyncio.apply()


DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE = 25 * 1024 * 1024
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

gpt_client = OpenAI(
    base_url="YOUR_GPT_API_BASE_URL_HERE",
    api_key="YOUR_ZUKIJOURNEY_API_KEY_HERE"
)
gemini_model = None
if GOOGLE_API_KEY and GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY_HERE":
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("Gemini AI Model initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Gemini AI Model: {e}")
        gemini_model = None
else:
    print("GOOGLE_API_KEY not set. Gemini command will not work.")
    gemini_model = None

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

stopwatches = {}
music_queue = []
currently_playing = {}

async def play_next_song(guild: discord.Guild):
    """Plays the next song in the queue for the guild."""
    voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    text_channel = discord.utils.get(guild.text_channels, name="music") or discord.utils.get(guild.text_channels, name="general") or guild.text_channels[0]

    if not music_queue:
        currently_playing.pop(guild.id, None)
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            if text_channel:
                try:
                    await text_channel.send("Queue finished. Disconnected from voice channel.")
                except discord.Forbidden:
                     print(f"Missing permissions to send message in {text_channel.name}")
        return

    if not voice_client or not voice_client.is_connected():
        if text_channel:
             try:
                await text_channel.send("Bot is not connected to a voice channel. Playback stopped.")
             except discord.Forbidden:
                print(f"Missing permissions to send message in {text_channel.name}")
        music_queue.clear()
        currently_playing.pop(guild.id, None)
        return

    if voice_client.is_playing() or voice_client.is_paused():
        return

    song_url = music_queue[0]
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(song_url, download=False))

            if 'entries' in info:
                info = info['entries'][0]

            audio_url = info.get('url')
            title = info.get('title', 'Unknown Title')
            if not audio_url:
                 raise ValueError("Could not extract audio stream URL.")

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        currently_playing[guild.id] = song_url

        def after_playing(error):
            if error:
                print(f"Player error in guild {guild.id}: {error}")
            if music_queue and currently_playing.get(guild.id) == music_queue[0]:
                 music_queue.pop(0)
            currently_playing.pop(guild.id, None)
            fut = asyncio.run_coroutine_threadsafe(play_next_song(guild), bot.loop)
            try:
                fut.result(timeout=5)
            except TimeoutError:
                 print(f"Warning: Timeout waiting for play_next_song task.")
            except Exception as e:
                print(f"Error scheduling next song in 'after' callback: {e}")

        voice_client.play(source, after=after_playing)

        if text_channel:
            try:
                await text_channel.send(f"Now playing: **{title}**")
            except discord.Forbidden:
                 print(f"Missing permissions to send 'Now playing' message.")

    except Exception as e:
        print(f"Error processing or playing song '{song_url}': {e}")
        if music_queue and song_url == music_queue[0]:
             music_queue.pop(0)
        currently_playing.pop(guild.id, None)
        if text_channel:
             try:
                 await text_channel.send(f"Error playing '{song_url}'. Skipping.")
             except discord.Forbidden:
                 print(f"Missing permissions to send error message.")
        asyncio.create_task(play_next_song(guild))


async def youtube_autocomplete(interaction: discord.Interaction, current: str):
    """Autocompletes Youtube queries for the /play command."""
    if not current:
        return []
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True, 'default_search': 'ytsearch10'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: ydl.extract_info(current, download=False))
            suggestions = []
            if results and 'entries' in results:
                for entry in results['entries'][:10]:
                    title = entry.get("title", "Unknown Title")
                    video_id = entry.get("id")
                    if video_id:
                         suggestions.append(app_commands.Choice(name=title[:99], value=video_id))
            return suggestions
    except Exception as e:
        print(f"YouTube autocomplete error: {e}")
        return []

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} application commands.")
    except Exception as e:
        print(f"Failed to sync application commands: {e}")
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f'Invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands')
    await bot.change_presence(activity=discord.Game(name="/help"))

@bot.event
async def on_message(message):
    """Handles messages to ignore self."""
    if message.author == bot.user:
        return

@bot.tree.command(name="gemini", description="Ask Gemini AI a question")
@app_commands.describe(prompt="What do you want to ask Gemini?")
async def gemini(interaction: discord.Interaction, prompt: str):
    # Responds to a prompt using the Gemini AI model.
    if not gemini_model:
        return await interaction.response.send_message("Gemini AI is not configured.", ephemeral=True)
    await interaction.response.defer()
    try:
        response = await gemini_model.generate_content_async(prompt)
        if not response.candidates:
             raise ValueError("No candidates received from Gemini.")
        if not hasattr(response.candidates[0], 'content') or not response.candidates[0].content.parts:
             raise ValueError("Invalid content structure in Gemini response.")
        if response.candidates[0].finish_reason != 1:
             raise ValueError(f"Gemini response finished unexpectedly.")

        reply = response.text.strip()
        if not reply: reply = "Received an empty response."

        if len(reply) <= 2000:
            await interaction.followup.send(reply)
        else:
            for i in range(0, len(reply), 2000):
                await interaction.followup.send(reply[i:i + 2000])
    except Exception as e:
        print(f"Gemini Error: {e}")
        await interaction.followup.send(f"An error occurred while contacting Gemini: {e}")


@bot.tree.command(name="timer", description="Set a countdown timer")
@app_commands.describe(seconds="How long in seconds?", label="Reminder label")
async def timer(interaction: discord.Interaction, seconds: int, label: str = "Time's up!"):
    # Sets a timer for a specified duration.
    if seconds <= 0:
        return await interaction.response.send_message("Seconds must be positive.", ephemeral=True)
    await interaction.response.send_message(f"Timer set for {seconds}s: {label}")
    await asyncio.sleep(seconds)
    await interaction.followup.send(f"{interaction.user.mention} {label}")

@bot.tree.command(name="stopwatch", description="Start/stop/reset stopwatch")
@app_commands.describe(action="start / stop / reset")
async def stopwatch(interaction: discord.Interaction, action: str):
    # Manages a simple stopwatch.
    user = interaction.user.id
    now = datetime.datetime.now()
    action = action.lower()

    if action == "start":
        stopwatches[user] = now
        await interaction.response.send_message("Stopwatch started.")
    elif action == "stop":
        if user in stopwatches:
            elapsed = now - stopwatches[user]
            total_seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            del stopwatches[user]
            await interaction.response.send_message(f"Stopwatch stopped. Elapsed: {elapsed_str}")
        else:
            await interaction.response.send_message("No stopwatch running for you.", ephemeral=True)
    elif action == "reset":
        if user in stopwatches:
            del stopwatches[user]
            await interaction.response.send_message("Stopwatch reset.")
        else:
            await interaction.response.send_message("No stopwatch was running to reset.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid action. Use 'start', 'stop', or 'reset'.", ephemeral=True)

@bot.tree.command(name="gpt", description="Ask a GPT model a question")
@app_commands.describe(prompt="What do you want to ask?")
async def gpt_command(interaction: discord.Interaction, prompt: str):
    # Gets a response from a generic GPT-like model endpoint.
    await interaction.response.defer()
    try:
        response = gpt_client.chat.completions.create(
            model="gpt-4o:online",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content.strip()
        if not reply:
            reply = "Received an empty response."

        if len(reply) <= 2000:
            await interaction.followup.send(reply)
        else:
            for i in range(0, len(reply), 2000):
                await interaction.followup.send(reply[i:i + 2000])
    except Exception as e:
        print(f"GPT API Error: {e}")
        await interaction.followup.send(f"An error occurred while contacting the API: {e}")

@bot.tree.command(name="alarm", description="Set an alarm (HH:MM in 24-hour format)")
@app_commands.describe(hour="Hour (0-23)", minute="Minute (0-59)", label="What should I remind you?")
async def alarm(interaction: discord.Interaction, hour: int, minute: int, label: str = "Alarm!"):
    # Sets an alarm for a specific time.
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return await interaction.response.send_message("Invalid hour or minute.", ephemeral=True)

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        target += datetime.timedelta(days=1)

    delay = (target - now).total_seconds()
    target_time_str = target.strftime('%H:%M')
    await interaction.response.send_message(f"Alarm set for {target_time_str} ({target.date()}) — {label}")

    await asyncio.sleep(delay)
    try:
        await interaction.followup.send(f"{interaction.user.mention} {label}")
    except discord.NotFound:
        print(f"Alarm interaction expired for {interaction.user}.")
        try:
            await interaction.channel.send(f"{interaction.user.mention} {label} (Alarm set at {target_time_str})")
        except Exception as ch_e:
             print(f"Failed to send alarm fallback message: {ch_e}")
    except Exception as e:
         print(f"Error sending alarm notification: {e}")


@bot.tree.command(name="mp3", description="Download audio from a YouTube link")
@app_commands.describe(url="Paste a YouTube video URL")
async def mp3(interaction: discord.Interaction, url: str):
    # Downloads the audio from a YouTube URL as an MP3 file.
    await interaction.response.defer(ephemeral=True)
    base_filename = os.path.join(DOWNLOAD_DIR, str(uuid.uuid4()))
    final_filename = base_filename + ".mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_filename + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': True,
        'noplaylist': True,
        'max_filesize': MAX_FILE_SIZE,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
            if not os.path.exists(final_filename):
                 possible_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(os.path.basename(base_filename)) and f.endswith(".mp3")]
                 if possible_files:
                     final_filename = os.path.join(DOWNLOAD_DIR, possible_files[0])
                 else:
                     raise FileNotFoundError("MP3 not found after conversion.")

    except yt_dlp.utils.DownloadError as e:
        if 'Unsupported URL' in str(e):
            return await interaction.followup.send("Error: Unsupported URL.", ephemeral=True)
        elif 'Video unavailable' in str(e):
            return await interaction.followup.send("Error: Video is unavailable.", ephemeral=True)
        elif 'age restricted' in str(e).lower():
             return await interaction.followup.send("Error: Video is age-restricted.", ephemeral=True)
        elif 'File is larger than max-filesize' in str(e):
             return await interaction.followup.send(f"Error: File larger than {MAX_FILE_SIZE // (1024*1024)}MB limit.", ephemeral=True)
        else:
             print(f"yt-dlp MP3 Download Error: {e}")
             return await interaction.followup.send(f"Download error occurred. Check URL.", ephemeral=True)
    except FileNotFoundError as e:
         print(f"MP3 File Not Found Error: {e}")
         return await interaction.followup.send("Error: Conversion to MP3 failed.", ephemeral=True)
    except Exception as e:
        print(f"Generic MP3 Download Error: {e}")
        return await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)

    if os.path.exists(final_filename):
        file_size = os.path.getsize(final_filename)
        if file_size < MAX_FILE_SIZE:
            await interaction.followup.send(f"MP3 downloaded:", file=discord.File(final_filename), ephemeral=False)
        else:
            await interaction.followup.send(f"File is too large for Discord.", ephemeral=True)
        try:
            os.remove(final_filename)
        except OSError as e:
            print(f"Error removing MP3 file {final_filename}: {e}")


@bot.tree.command(name="mp4", description="Download video from a YouTube link")
@app_commands.describe(url="Paste a YouTube video URL")
async def mp4(interaction: discord.Interaction, url: str):
    # Downloads a YouTube video as an MP4 file.
    await interaction.response.defer(ephemeral=True)
    filename = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp4")
    ydl_opts = {
        'format': f'bestvideo[ext=mp4][filesize<{MAX_FILE_SIZE}]+bestaudio[ext=m4a]/best[ext=mp4][filesize<{MAX_FILE_SIZE}]/best[filesize<{MAX_FILE_SIZE}]',
        'outtmpl': filename,
        'quiet': True,
        'noplaylist': True,
         'max_filesize': MAX_FILE_SIZE,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
    except yt_dlp.utils.DownloadError as e:
         if 'Unsupported URL' in str(e): return await interaction.followup.send("Error: Unsupported URL.", ephemeral=True)
         if 'Video unavailable' in str(e): return await interaction.followup.send("Error: Video unavailable.", ephemeral=True)
         if 'age restricted' in str(e).lower(): return await interaction.followup.send("Error: Video is age-restricted.", ephemeral=True)
         if 'Requested format is not available' in str(e): return await interaction.followup.send("Error: Suitable video format not found.", ephemeral=True)
         if 'File is larger than max-filesize' in str(e): return await interaction.followup.send(f"Error: File larger than {MAX_FILE_SIZE // (1024*1024)}MB limit.", ephemeral=True)
         print(f"yt-dlp MP4 Download Error: {e}")
         return await interaction.followup.send(f"Download error occurred.", ephemeral=True)
    except Exception as e:
        print(f"Generic MP4 Download Error: {e}")
        return await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)

    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if file_size < MAX_FILE_SIZE:
            await interaction.followup.send(f"MP4 downloaded:", file=discord.File(filename), ephemeral=False)
        else:
            await interaction.followup.send(f"File is too large for Discord.", ephemeral=True)
        try:
            os.remove(filename)
        except OSError as e:
            print(f"Error removing MP4 file {filename}: {e}")
    else:
        await interaction.followup.send("Failed to download video.", ephemeral=True)


@bot.tree.command(name="play", description="Play a song from YouTube")
@app_commands.describe(query="Song name or YouTube URL/ID")
@app_commands.autocomplete(query=youtube_autocomplete)
async def play(interaction: discord.Interaction, query: str):
    """Plays a song from a query, URL, or video ID."""
    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        return await interaction.response.send_message("You need to be in a voice channel.", ephemeral=True)

    await interaction.response.defer()

    channel = voice_state.channel
    voice_client = interaction.guild.voice_client

    if not voice_client:
        try:
            voice_client = await channel.connect()
        except Exception as e:
            return await interaction.followup.send(f"Failed to connect to voice channel: {e}")
    elif voice_client.channel != channel:
        try:
            await voice_client.move_to(channel)
        except Exception as e:
            return await interaction.followup.send(f"Failed to move to voice channel: {e}")

    if len(query) == 11 and not query.startswith("http"):
         video_url = f"https://www.youtube.com/watch?v={query}"
         title = query
         try:
             ydl_opts_title = {'quiet': True, 'extract_flat': True}
             with yt_dlp.YoutubeDL(ydl_opts_title) as ydl:
                 info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(video_url, download=False))
                 title = info.get('title', query)
         except Exception: pass
         feedback_query = title
    else:
         video_url = query
         feedback_query = query

    music_queue.append(video_url)
    queue_pos = len(music_queue)

    if not voice_client.is_playing() and not voice_client.is_paused():
        await interaction.followup.send(f"Adding **{feedback_query}** and starting playback...")
        asyncio.create_task(play_next_song(interaction.guild))
    else:
        await interaction.followup.send(f"Added **{feedback_query}** to position #{queue_pos} in the queue.")


@bot.tree.command(name="leave", description="Leave the voice channel")
async def leave(interaction: discord.Interaction):
    # Disconnects the bot from the voice channel.
    voice_client = interaction.guild.voice_client
    if voice_client:
        if voice_client.is_playing() or voice_client.is_paused():
             voice_client.stop()
        music_queue.clear()
        currently_playing.pop(interaction.guild.id, None)
        await voice_client.disconnect()
        await interaction.response.send_message("Left the voice channel.")
    else:
        await interaction.response.send_message("Not in a voice channel.", ephemeral=True)


@bot.tree.command(name="pause", description="Pause the currently playing music")
async def pause(interaction: discord.Interaction):
    # Pauses the current music playback.
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Music paused.")
    elif voice_client and voice_client.is_paused():
         await interaction.response.send_message("Music is already paused.", ephemeral=True)
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)


@bot.tree.command(name="resume", description="Resume the paused music")
async def resume(interaction: discord.Interaction):
    # Resumes the paused music.
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Music resumed.")
    elif voice_client and voice_client.is_playing():
        await interaction.response.send_message("Music is already playing.", ephemeral=True)
    else:
        await interaction.response.send_message("Music is not paused or playing.", ephemeral=True)


@bot.tree.command(name="stop", description="Stop the music and clear the queue")
async def stop(interaction: discord.Interaction):
    # Stops music and clears the queue.
    voice_client = interaction.guild.voice_client
    guild_id = interaction.guild.id
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        music_queue.clear()
        currently_playing.pop(guild_id, None)
        voice_client.stop()
        await interaction.response.send_message("Music stopped and queue cleared.")
    else:
        await interaction.response.send_message("No music is currently playing or paused.", ephemeral=True)


@bot.tree.command(name="queue", description="Shows the current music queue")
async def queue(interaction: discord.Interaction):
    # Displays the current music queue.
    guild_id = interaction.guild.id
    embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
    current_song_url = currently_playing.get(guild_id)
    if current_song_url:
        title = current_song_url
        try:
            ydl_opts_q = {'quiet': True, 'extract_flat': True, 'force_generic_extractor': True}
            with yt_dlp.YoutubeDL(ydl_opts_q) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(current_song_url, download=False))
                title = info.get('title', current_song_url)
        except Exception: pass
        embed.add_field(name="Now Playing", value=f"[{title}]({current_song_url})", inline=False)
    else:
        embed.add_field(name="Now Playing", value="Nothing playing.", inline=False)

    if music_queue:
        queue_list = []
        for i, item in enumerate(music_queue[:15]):
            queue_list.append(f"{i+1}. `{item}`")
        queue_str = "\n".join(queue_list)
        if len(music_queue) > 15:
            queue_str += f"\n... and {len(music_queue) - 15} more."
        embed.add_field(name="Up Next", value=queue_str, inline=False)
    else:
         embed.add_field(name="Up Next", value="Queue is empty.", inline=False)

    embed.set_footer(text=f"Total songs in queue: {len(music_queue)}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="skip", description="Skip the currently playing song")
async def skip(interaction: discord.Interaction):
    """Skips the current song by stopping the player."""
    voice_client = interaction.guild.voice_client
    guild_id = interaction.guild.id

    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)

    if not voice_client.is_playing() and not voice_client.is_paused():
        return await interaction.response.send_message("No song is playing to skip.", ephemeral=True)

    voice_client.stop()
    await interaction.response.send_message("Skipped the current song.")

@bot.tree.command(name="removelastsong", description="Removes last song from queue")
async def removelastsong(interaction: discord.Interaction):
    # Removes the most recently added song from the queue.
    if music_queue:
        removed_song = music_queue.pop()
        await interaction.response.send_message(f"Removed `{removed_song}` from the queue.")
    else:
        await interaction.response.send_message("The queue is already empty.", ephemeral=True)

@bot.tree.command(name="help", description="Show available commands and usage")
async def help_command(interaction: discord.Interaction):
    # Shows the help message with all commands.
    embed = discord.Embed(
        title="Bot Help",
        description="Here are all the available slash commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="/gemini",value="Ask Gemini AI a question.",inline=False)
    embed.add_field(name="/gpt",value="Ask a GPT model a question.",inline=False)
    embed.add_field(name="/mp3 <url>", value="Download audio (MP3).", inline=False)
    embed.add_field(name="/mp4 <url>", value="Download video (MP4).", inline=False)
    embed.add_field(name="/timer <seconds> <label>", value="Start a countdown timer.", inline=False)
    embed.add_field(name="/stopwatch <start|stop|reset>", value="Basic stopwatch.", inline=False)
    embed.add_field(name="/alarm <hour> <minute> <label>", value="Set an alarm.", inline=False)
    embed.add_field(name="/play <query>", value="Play a song from YouTube.", inline=False)
    embed.add_field(name="/leave", value="Leave the voice channel.", inline=False)
    embed.add_field(name="/pause", value="Pause the music.", inline=False)
    embed.add_field(name="/resume", value="Resume the music.", inline=False)
    embed.add_field(name="/stop", value="Stop music & clear queue.", inline=False)
    embed.add_field(name="/queue", value="Show the music queue.", inline=False)
    embed.add_field(name="/skip", value="Skip the current song.", inline=False)
    embed.add_field(name="/removelastsong", value="Removes last song from queue.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    if "YOUR_DISCORD_BOT_TOKEN_HERE" in DISCORD_BOT_TOKEN or not DISCORD_BOT_TOKEN:
        print("CRITICAL: DISCORD_BOT_TOKEN is missing or is a placeholder.")
        print("Please set the token correctly in the script.")
    else:
        try:
            print("Attempting to run bot...")
            if gemini_model is None:
                 print("Note: Gemini AI features will be unavailable.")
            bot.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            print("Discord Login Failed: Token is invalid or intents missing.")
        except Exception as e:
            print(f"An unexpected error occurred during bot startup: {e}")
            print(f"Error Type: {type(e)}")