import os
import re
import sys
import asyncio
import aiofiles
import aiohttp
import time
import json
import logging
from typing import List, Tuple, Optional
from pathlib import Path

import requests
import yt_dlp
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode

from aiohttp import ClientSession, web
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from pyromod import listen

# Import your custom modules
from logs import logging
import saini as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER, CREDIT, AUTH_USERS, TOTAL_USERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Global variables with improved management
class BotState:
    def __init__(self):
        self.processing_request = False
        self.cancel_requested = False
        self.cancel_message = None
        self.caption = '/d'
        self.vidwatermark = '/d'
        self.topic = '/d'
        
        # Tokens from environment variables with fallbacks
        self.cwtoken = os.getenv('CW_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg')
        self.cptoken = os.getenv('CP_TOKEN', 'cptoken')
        self.pwtoken = os.getenv('PW_TOKEN', 'pwtoken')
        self.adda_token = os.getenv('ADDA_TOKEN', 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkcGthNTQ3MEBnbWFpbC5jb20iLCJhdWQiOiIxNzg2OTYwNSIsImlhdCI6MTc0NDk0NDQ2NCwiaXNzIjoiYWRkYTI0Ny5jb20iLCJuYW1lIjoiZHBrYSIsImVtYWlsIjoiZHBrYTU0NzBAZ21haWwuY29tIiwicGhvbmUiOiI3MzUyNDA0MTc2IiwidXNlcklkIjoiYWRkYS52MS41NzMyNmRmODVkZDkxZDRiNDkxN2FiZDExN2IwN2ZjOCIsImxvZ2luQXBpVmVyc2lvbiI6MX0.0QOuYFMkCEdVmwMVIPeETa6Kxr70zEslWOIAfC_ylhbku76nDcaBoNVvqN4HivWNwlyT0jkUKjWxZ8AbdorMLg')
        
        # File paths
        self.cookies_file_path = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # API configuration
        self.api_url = "http://master-api-v3.vercel.app/"
        self.api_token = os.getenv('API_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I')

# Initialize bot state
bot_state = BotState()

# Constants
PHOTO_URLS = {
    "main": "https://files.catbox.moe/8e2qqw.jpg",
    "commands": "https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
    "features": "https://tinypic.host/images/2025/07/14/file_000000002d44622f856a002a219cf27aconversation_id68747543-56d8-800e-ae47-bb6438a09851message_id8e8cbfb5-ea6c-4f59-974a-43bdf87130c0.png",
    "youtube": "https://envs.sh/GVi.jpg",
    "upgrade": "https://envs.sh/GVI.jpg"
}

BUTTONSCONTACT = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="📞 Contact", url="https://t.me/saini_contact_bot")]
])

# Utility Functions
async def safe_delete_message(message: Message):
    """Safely delete a message with error handling."""
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")

async def safe_remove_file(file_path: str):
    """Safely remove a file with error handling."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning(f"Failed to remove file {file_path}: {e}")

async def download_file_with_retry(url: str, file_path: str, max_retries: int = 3) -> bool:
    """Download file with retry mechanism."""
    for attempt in range(max_retries):
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                async with aiofiles.open(file_path, 'wb') as file:
                    await file.write(response.content)
                return True
            else:
                logger.warning(f"Download attempt {attempt + 1} failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2)
    
    return False

async def execute_command_async(cmd: str) -> Tuple[bool, str]:
    """Execute shell command asynchronously."""
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True, stdout.decode('utf-8', errors='ignore')
        else:
            return False, stderr.decode('utf-8', errors='ignore')
            
    except Exception as e:
        return False, str(e)

def validate_user_input(raw_text: str, max_value: int) -> int:
    """Validate user input for numeric values."""
    try:
        value = int(raw_text)
        if 1 <= value <= max_value:
            return value
        return 1
    except (ValueError, TypeError):
        return 1

async def process_links_content(content: str) -> Tuple[List[Tuple[str, str]], dict]:
    """Process links content and return links with statistics."""
    links = []
    stats = {
        'pdf_count': 0, 'img_count': 0, 'v2_count': 0, 'mpd_count': 0,
        'm3u8_count': 0, 'yt_count': 0, 'drm_count': 0, 'zip_count': 0,
        'other_count': 0, 'total_count': 0
    }
    
    for line in content.split("\n"):
        if "://" in line:
            parts = line.split("://", 1)
            if len(parts) == 2:
                links.append((parts[0], parts[1]))
                url = parts[1]
                
                # Count by type
                if ".pdf" in url:
                    stats['pdf_count'] += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    stats['img_count'] += 1
                elif "v2" in url:
                    stats['v2_count'] += 1
                elif "mpd" in url:
                    stats['mpd_count'] += 1
                elif "m3u8" in url:
                    stats['m3u8_count'] += 1
                elif "drm" in url:
                    stats['drm_count'] += 1
                elif "youtu" in url:
                    stats['yt_count'] += 1
                elif "zip" in url:
                    stats['zip_count'] += 1
                else:
                    stats['other_count'] += 1
                    
                stats['total_count'] += 1
    
    return links, stats

# Bot Handlers
@bot.on_message(filters.command("addauth") & filters.private)
async def add_auth_user(client: Client, message: Message):
    """Add user to authorized users list."""
    if message.chat.id != OWNER:
        return
    
    try:
        if len(message.command) < 2:
            await message.reply_text("**Please provide a valid user ID.**")
            return
            
        new_user_id = int(message.command[1])
        if new_user_id in AUTH_USERS:
            await message.reply_text("**User ID is already authorized.**")
        else:
            AUTH_USERS.append(new_user_id)
            await message.reply_text(f"**User ID `{new_user_id}` added to authorized users.**")
            try:
                await bot.send_message(chat_id=new_user_id, text=f"<b>Great! You are added in Premium Membership!</b>")
            except Exception as e:
                logger.warning(f"Could not notify user {new_user_id}: {e}")
    except (IndexError, ValueError):
        await message.reply_text("**Please provide a valid user ID.**")

@bot.on_message(filters.command("users") & filters.private)
async def list_auth_users(client: Client, message: Message):
    """List all authorized users."""
    if message.chat.id != OWNER:
        return
    
    user_list = '\n'.join(map(str, AUTH_USERS))
    await message.reply_text(f"**Authorized Users:**\n{user_list}")

@bot.on_message(filters.command("rmauth") & filters.private)
async def remove_auth_user(client: Client, message: Message):
    """Remove user from authorized users list."""
    if message.chat.id != OWNER:
        return
    
    try:
        if len(message.command) < 2:
            await message.reply_text("**Please provide a valid user ID.**")
            return
            
        user_id_to_remove = int(message.command[1])
        if user_id_to_remove not in AUTH_USERS:
            await message.reply_text("**User ID is not in the authorized users list.**")
        else:
            AUTH_USERS.remove(user_id_to_remove)
            await message.reply_text(f"**User ID `{user_id_to_remove}` removed from authorized users.**")
            try:
                await bot.send_message(chat_id=user_id_to_remove, text=f"<b>Oops! You are removed from Premium Membership!</b>")
            except Exception as e:
                logger.warning(f"Could not notify user {user_id_to_remove}: {e}")
    except (IndexError, ValueError):
        await message.reply_text("**Please provide a valid user ID.**")

@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_handler(client: Client, message: Message):
    """Broadcast message to all users."""
    if message.chat.id != OWNER:
        return
        
    if not message.reply_to_message:
        await message.reply_text("**Reply to any message (text, photo, video, or file) with /broadcast to send it to all users.**")
        return
        
    success = 0
    fail = 0
    unique_users = list(set(TOTAL_USERS))
    
    for user_id in unique_users:
        try:
            if message.reply_to_message.text:
                await client.send_message(user_id, message.reply_to_message.text)
            elif message.reply_to_message.photo:
                await client.send_photo(
                    user_id,
                    photo=message.reply_to_message.photo.file_id,
                    caption=message.reply_to_message.caption or ""
                )
            elif message.reply_to_message.video:
                await client.send_video(
                    user_id,
                    video=message.reply_to_message.video.file_id,
                    caption=message.reply_to_message.caption or ""
                )
            elif message.reply_to_message.document:
                await client.send_document(
                    user_id,
                    document=message.reply_to_message.document.file_id,
                    caption=message.reply_to_message.caption or ""
                )
            else:
                await client.forward_messages(user_id, message.chat.id, message.reply_to_message.id)

            success += 1
            await asyncio.sleep(0.1)  # Prevent flooding
            
        except (FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated):
            fail += 1
        except Exception as e:
            logger.error(f"Broadcast failed for {user_id}: {e}")
            fail += 1

    await message.reply_text(
        f"<b>Broadcast complete!</b>\n<blockquote><b>✅ Success: {success}\n❎ Failed: {fail}</b></blockquote>"
                )
    @bot.on_message(filters.command("broadusers") & filters.private)
async def broadusers_handler(client: Client, message: Message):
    """List all broadcast users."""
    if message.chat.id != OWNER:
        return

    if not TOTAL_USERS:
        await message.reply_text("**No Broadcasted User**")
        return

    user_infos = []
    for user_id in list(set(TOTAL_USERS)):
        try:
            user = await client.get_users(int(user_id))
            fname = user.first_name if user.first_name else " "
            user_infos.append(f"[{user.id}](tg://openmessage?user_id={user.id}) | `{fname}`")
        except Exception as e:
            logger.warning(f"Could not get user info for {user_id}: {e}")
            user_infos.append(f"[{user.id}](tg://openmessage?user_id={user.id})")

    total = len(user_infos)
    text = (
        f"<blockquote><b>Total Users: {total}</b></blockquote>\n\n"
        "<b>Users List:</b>\n" + "\n".join(user_infos)
    )
    await message.reply_text(text)

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, message: Message):
    """Handle cookies file upload."""
    editable = await message.reply_text(
        "**Please upload the YouTube Cookies file (.txt format).**",
        quote=True
    )

    try:
        input_message: Message = await client.listen(message.chat.id, timeout=60)

        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await message.reply_text("Invalid file type. Please upload a .txt file.")
            return

        downloaded_path = await input_message.download()
        
        try:
            async with aiofiles.open(downloaded_path, "r") as uploaded_file:
                cookies_content = await uploaded_file.read()

            async with aiofiles.open(bot_state.cookies_file_path, "w") as target_file:
                await target_file.write(cookies_content)

            await editable.edit("✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`.")
            
        except Exception as e:
            await message.reply_text(f"Error processing cookies file: {str(e)}")
        finally:
            await safe_remove_file(downloaded_path)
            await safe_delete_message(input_message)

    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No file received within 60 seconds.**")
    except Exception as e:
        await message.reply_text(f"**Failed to update cookies:**\n<blockquote>{str(e)}</blockquote>")

@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client: Client, message: Message):
    """Convert text to .txt file."""
    user_id = str(message.from_user.id)
    
    editable = await message.reply_text(
        "<blockquote><b>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</b></blockquote>"
    )
    
    try:
        input_message: Message = await client.listen(message.chat.id, timeout=60)
        if not input_message.text:
            await message.reply_text("**Send valid text data**")
            return

        text_data = input_message.text.strip()
        await safe_delete_message(input_message)
        
        await editable.edit("**🔄 Send file name or send /d for filename**")
        input_name: Message = await client.listen(message.chat.id, timeout=30)
        raw_text_name = input_name.text
        await safe_delete_message(input_name)
        await safe_delete_message(editable)

        custom_file_name = 'txt_file' if raw_text_name == '/d' else raw_text_name
        txt_file = bot_state.downloads_dir / f'{custom_file_name}.txt'

        async with aiofiles.open(txt_file, 'w', encoding='utf-8') as f:
            await f.write(text_data)
        
        await message.reply_document(
            document=str(txt_file),
            caption=f"`{custom_file_name}.txt`\n\n<blockquote>You can now download your content! 📥</blockquote>"
        )
        
    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No input received.**")
    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")
    finally:
        await safe_remove_file(str(txt_file))

@bot.on_message(filters.command(["y2t"]))
async def youtube_to_txt(client: Client, message: Message):
    """Convert YouTube playlist to .txt file."""
    user_id = str(message.from_user.id)
    
    editable = await message.reply_text(
        "<blockquote><b>Send YouTube Website/Playlist link for convert in .txt file</b></blockquote>"
    )

    try:
        input_message: Message = await client.listen(message.chat.id, timeout=60)
        youtube_link = input_message.text.strip()
        await safe_delete_message(input_message)
        await safe_delete_message(editable)

        # Fetch YouTube information using yt-dlp with cookies
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'force_generic_extractor': True,
            'forcejson': True,
            'cookies': bot_state.cookies_file_path
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(youtube_link, download=False)
                title = result.get('title', 'youtube_content').replace(' ', '_')
            except yt_dlp.utils.DownloadError as e:
                await message.reply_text(f"<blockquote>YouTube DL Error: {str(e)}</blockquote>")
                return

        # Extract YouTube links
        videos = []
        if 'entries' in result:
            for entry in result['entries']:
                video_title = entry.get('title', 'No title')
                url = entry['url']
                videos.append(f"{video_title}: {url}")
        else:
            video_title = result.get('title', 'No title')
            url = result['url']
            videos.append(f"{video_title}: {url}")

        # Create and save the .txt file
        txt_file = bot_state.downloads_dir / f'{title}.txt'
        async with aiofiles.open(txt_file, 'w', encoding='utf-8') as f:
            await f.write('\n'.join(videos))

        # Send the generated text file
        await message.reply_document(
            document=str(txt_file),
            caption=f'<a href="{youtube_link}">__**Click Here to Open Link**__</a>\n<blockquote>{title}.txt</blockquote>\n'
        )

    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No link received.**")
    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")
    finally:
        await safe_remove_file(str(txt_file))

@bot.on_message(filters.command(["ytm"]))
async def youtube_music_handler(client: Client, message: Message):
    """Download YouTube videos as MP3."""
    if bot_state.processing_request:
        await message.reply_text("**Another process is already running. Please wait.**")
        return
        
    bot_state.processing_request = True
    bot_state.cancel_requested = False
    
    try:
        editable = await message.reply_text(
            "__**Input Type**__\n\n<blockquote><b>01 •Send me the .txt file containing YouTube links\n02 •Send Single link or Set of YouTube multiple links</b></blockquote>"
        )
        
        input_msg: Message = await client.listen(message.chat.id, timeout=60)
        
        links = []
        playlist_name = "YouTube_Music"
        
        if input_msg.document and input_msg.document.file_name.endswith(".txt"):
            file_path = await input_msg.download()
            try:
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                content_lines = content.split("\n")
                
                for line in content_lines:
                    if "://" in line:
                        parts = line.split("://", 1)
                        if len(parts) == 2:
                            links.append(parts)
                
                file_name = Path(file_path).stem
                playlist_name = file_name.replace('_', ' ')
                
            except Exception as e:
                await message.reply_text("**Invalid file input.**")
                return
            finally:
                await safe_remove_file(file_path)
                
            await editable.edit(f"**•ᴛᴏᴛᴀʟ 🔗 ʟɪɴᴋs ғᴏᴜɴᴅ ᴀʀᴇ --__{len(links)}__--\n•sᴇɴᴅ ғʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ**")
            
            try:
                input_start: Message = await client.listen(editable.chat.id, timeout=20)
                raw_text = input_start.text
                await safe_delete_message(input_start)
            except asyncio.TimeoutError:
                raw_text = '1'
                
            start_index = validate_user_input(raw_text, len(links))
            
            try:
                if start_index == 1:
                    playlist_message = await message.reply_text(f"<blockquote><b>⏯️Playlist : {playlist_name}</b></blockquote>")
                    await client.pin_chat_message(message.chat.id, playlist_message.id)
            except Exception:
                pass
                
        elif input_msg.text:
            content = input_msg.text.strip().split("\n")
            for line in content:
                if "://" in line:
                    parts = line.split("://", 1)
                    if len(parts) == 2:
                        links.append(parts)
            start_index = 1
            await safe_delete_message(input_msg)
        else:
            await message.reply_text("**Invalid input. Send either a .txt file or YouTube links set**")
            return
            
        await safe_delete_message(editable)
        
        count = start_index
        for i in range(start_index - 1, len(links)):
            if bot_state.cancel_requested:
                await message.reply_text("🚦**STOPPED**🚦")
                break
                
            try:
                Vxy = links[i][1].replace("www.youtube-nocookie.com/embed", "youtu.be")
                url = "https://" + Vxy
                
                # Get video title
                oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                response = requests.get(oembed_url)
                audio_title = response.json().get('title', 'YouTube Video')
                audio_title = audio_title.replace("_", " ")
                name = f'{audio_title[:60]} {CREDIT}'
                name1 = f'{audio_title} {CREDIT}'

                if "youtube.com" in url or "youtu.be" in url:
                    prog = await message.reply_text(
                        f"<i><b>Audio Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    )
                    
                    cmd = f'yt-dlp -x --audio-format mp3 --cookies {bot_state.cookies_file_path} "{url}" -o "{name}.mp3"'
                    success, output = await execute_command_async(cmd)
                    
                    if success and Path(f'{name}.mp3').exists():
                        await safe_delete_message(prog)
                        try:
                            await client.send_document(
                                chat_id=message.chat.id,
                                document=f'{name}.mp3',
                                caption=f'**🎵 Title : **[{str(count).zfill(3)}] - {name1}.mp3\n\n🔗**Video link** : {url}\n\n🌟** Extracted By** : {CREDIT}'
                            )
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to send audio {name}: {e}")
                            await message.reply_text(
                                f'⚠️**Upload Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}',
                                disable_web_page_preview=True
                            )
                            count += 1
                        finally:
                            await safe_remove_file(f'{name}.mp3')
                    else:
                        await safe_delete_message(prog)
                        await message.reply_text(
                            f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}',
                            disable_web_page_preview=True
                        )
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error processing link {i}: {e}")
                await message.reply_text(
                    f'⚠️**Processing Failed**⚠️\n**Url** =>> {url}\n**Error** =>> {str(e)}',
                    disable_web_page_preview=True
                )
                count += 1
                
    except Exception as e:
        await message.reply_text(f"<b>Failed Reason:</b>\n<blockquote><b>{str(e)}</b></blockquote>")
    finally:
        bot_state.processing_request = False
        bot_state.cancel_requested = False
        await message.reply_text("<blockquote><b>YouTube Music Download Process Completed</b></blockquote>")

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, message: Message):
    """Send cookies file to user."""
    try:
        if Path(bot_state.cookies_file_path).exists():
            await client.send_document(
                chat_id=message.chat.id,
                document=bot_state.cookies_file_path,
                caption="Here is the `youtube_cookies.txt` file."
            )
        else:
            await message.reply_text("Cookies file not found.")
    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command("caption") & filters.private)
async def caption_handler(client: Client, message: Message):
    """Set caption style."""
    editable = await message.reply_text(
        "**Caption Style**\n\n<b>01 •Send /d for Default Caption Style.\n02. •Send /simple for Simple Caption Style.</b>"
    )
    
    try:
        input_cap: Message = await client.listen(message.chat.id, timeout=30)
        bot_state.caption = input_cap.text
        
        if bot_state.caption == '/d':
            await editable.edit("**Caption Set in Default Style ✅**")
        else:
            await editable.edit("**Caption Set in Normal Style ✅**")
            
        await safe_delete_message(input_cap)
    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No input received.**")

@bot.on_message(filters.command("vidwatermark") & filters.private)
async def vidwatermark_handler(client: Client, message: Message):
    """Set video watermark."""
    editable = await message.reply_text("**Send Video Watermark text, else Send /d**")
    
    try:
        input_watermark: Message = await client.listen(message.chat.id, timeout=30)
        bot_state.vidwatermark = input_watermark.text
        
        if bot_state.vidwatermark == '/d':
            await editable.edit("**Video Watermark Disabled ✅**")
        else:
            await editable.edit(f"**Video Watermark Enabled ✅\nWatermark Text - {bot_state.vidwatermark}**")
            
        await safe_delete_message(input_watermark)
    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No input received.**")

@bot.on_message(filters.command("topic") & filters.private)
async def topic_handler(client: Client, message: Message):
    """Set topic-wise uploading."""
    editable = await message.reply_text(
        "**If you want to topic wise uploader : send `yes` or send /d**\n\n<blockquote><b>Topic fetch from (bracket) in title</b></blockquote>"
    )
    
    try:
        input_topic: Message = await client.listen(message.chat.id, timeout=30)
        bot_state.topic = input_topic.text
        
        if bot_state.topic == "yes":
            await editable.edit("**Topic Wise Uploading On ✅**")
        else:
            await editable.edit("**Topic Wise Uploading Off ✅**")
            
        await safe_delete_message(input_topic)
    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No input received.**")
        @bot.on_message(filters.command("token") & filters.private)
async def token_handler(client: Client, message: Message):
    """Update tokens."""
    editable = await message.reply_text("<b>Enter 𝐏𝐖/𝐂𝐖/𝐂𝐏 Working Token For 𝐌𝐏𝐃 𝐔𝐑𝐋 or send /d</b>")
    
    try:
        input_token: Message = await client.listen(message.chat.id, timeout=30)
        token = input_token.text
        
        if token == '/d':
            # Reset to default tokens
            bot_state.cwtoken = os.getenv('CW_TOKEN', 'default_cw_token')
            bot_state.cptoken = os.getenv('CP_TOKEN', 'cptoken')
            bot_state.pwtoken = os.getenv('PW_TOKEN', 'pwtoken')
            await editable.edit("**Default Token Used ✅**")
        else:
            bot_state.cwtoken = token
            bot_state.cptoken = token
            bot_state.pwtoken = token
            await editable.edit("**Updated Token Used ✅**")
            
        await safe_delete_message(input_token)
    except asyncio.TimeoutError:
        await editable.edit("**Timeout: No input received.**")

@bot.on_message(filters.command(["reset"]))
async def restart_handler(client: Client, message: Message):
    """Reset the bot."""
    if message.chat.id != OWNER:
        return
        
    await message.reply_text("𝐁𝐨𝐭 𝐢𝐬 𝐑𝐞𝐬𝐞𝐭𝐢𝐧𝐠...", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("stop") & filters.private)
async def cancel_handler(client: Client, message: Message):
    """Cancel ongoing process."""
    if message.chat.id not in AUTH_USERS:
        await client.send_message(
            message.chat.id,
            f"<blockquote>__**Oopss! You are not a Premium member**__\n"
            f"__**PLEASE /upgrade YOUR PLAN**__\n"
            f"__**Send me your user id for authorization**__\n"
            f"__**Your User id** __- `{message.chat.id}`</blockquote>\n\n"
        )
        return
        
    if bot_state.processing_request:
        bot_state.cancel_requested = True
        await safe_delete_message(message)
        bot_state.cancel_message = await message.reply_text("**🚦 Process cancel request received. Stopping after current process...**")
    else:
        await message.reply_text("**⚡ No active process to cancel.**")

@bot.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    """Start command handler."""
    user_id = message.chat.id
    if user_id not in TOTAL_USERS:
        TOTAL_USERS.append(user_id)
        
    user = await client.get_me()
    caption = f"🌟 Welcome {message.from_user.mention} ! 🌟"
    
    start_message = await client.send_photo(
        chat_id=message.chat.id,
        photo=PHOTO_URLS["main"],
        caption=caption
    )

    # Progress animation
    progress_steps = [
        ("Initializing Uploader bot... 🤖", 0),
        ("Loading features... ⏳", 25),
        ("This may take a moment, sit back and relax! 😊", 50),
        ("Checking subscription status... 🔍", 75),
        ("Setup complete! 🎉", 100)
    ]
    
    for text, progress in progress_steps:
        await asyncio.sleep(1)
        progress_bar = "🟩" * (progress // 10) + "⬜️" * (10 - progress // 10)
        await start_message.edit_text(
            f"🌟 Welcome {message.from_user.first_name}! 🌟\n\n" +
            f"{text}\n\n"
            f"Progress: [{progress_bar}] {progress}%\n\n"
        )

    # Final message based on user status
    if message.chat.id in AUTH_USERS:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("🕸️ Commands", callback_data="cmd_command")],
            [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
            [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")],
        ])
        
        await start_message.edit_text(
            f"🌟 Welcome {message.from_user.first_name}! 🌟\n\n" +
            f"Great! You are a premium member!\n"
            f"Use button : **✨ Commands** to get started 🌟\n\n"
            f"If you face any problem contact -  [{CREDIT}⁬](tg://openmessage?user_id={OWNER})\n",
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
            [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
            [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")],
        ])
        
        await start_message.edit_text(
           f" 🎉 Welcome {message.from_user.first_name} to DRM Bot! 🎉\n\n"
           f"**You are currently using the free version.** 🆓\n\n<blockquote expandable>I'm here to make your life easier by downloading videos from your **.txt** file 📄 and uploading them directly to Telegram!</blockquote>\n\n**Want to get started? Press /id**\n\n💬 Contact : [{CREDIT}⁬](tg://openmessage?user_id={OWNER}) to Get The Subscription 🎫 and unlock the full potential of your new bot! 🔓\n",
           disable_web_page_preview=True,
           reply_markup=keyboard
        )

@bot.on_callback_query(filters.regex("back_to_main_menu"))
async def back_to_main_menu(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    caption = f"✨ **Welcome [{first_name}](tg://user?id={user_id}) in My uploader bot**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
        [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
        [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")],
    ])
    
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["main"], caption=caption),
        reply_markup=keyboard
    )
    await callback_query.answer()

@bot.on_callback_query(filters.regex("cmd_command"))
async def cmd_command_handler(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    caption = f"✨ **Welcome [{first_name}](tg://user?id={user_id})\nChoose Button to select Commands**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚻 User", callback_data="user_command"), InlineKeyboardButton("🚹 Owner", callback_data="owner_command")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["commands"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("user_command"))
async def help_button(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Commands", callback_data="cmd_command")]])
    caption = (
        f"💥 𝐁𝐎𝐓𝐒 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" 
        f"📌 𝗠𝗮𝗶𝗻 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:\n\n"  
        f"➥ /start – Bot Status Check\n"
        f"➥ /drm – Extract from .txt (Auto)\n"
        f"➥ /y2t – YouTube → .txt Converter\n"  
        f"➥ /ytm – YouTube → .mp3 downloader\n"  
        f"➥ /t2t – Text → .txt Generator\n" 
        f"➥ /stop – Cancel Running Task\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰ \n" 
        f"⚙️ 𝗧𝗼𝗼𝗹𝘀 & 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀: \n\n" 
        f"➥ /cookies – Update YT Cookies\n" 
        f"➥ /id – Get Chat/User ID\n"  
        f"➥ /info – User Details\n"  
        f"➥ /logs – View Bot Activity\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        f"💡 𝗡𝗼𝘁𝗲:\n\n"  
        f"• Send any link for auto-extraction\n"  
        f"• Supports batch processing\n\n"  
        f"╭────────⊰◆⊱────────╮\n"   
        f" ➠ 𝐌𝐚𝐝𝐞 𝐁𝐲 : {CREDIT} 💻\n"
        f"╰────────⊰◆⊱────────╯\n"
    )
    
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["commands"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("owner_command"))
async def help_button(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Commands", callback_data="cmd_command")]])
    caption = (
        f"👤 𝐁𝐨𝐭 𝐎𝐰𝐧𝐞𝐫 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬\n\n" 
        f"➥ /addauth xxxx – Add User ID\n" 
        f"➥ /rmauth xxxx – Remove User ID\n"  
        f"➥ /users – Total User List\n"  
        f"➥ /broadcast – For Broadcasting\n"  
        f"➥ /broadusers – All Broadcasting Users\n"  
        f"➥ /reset – Reset Bot\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"  
        f"╭────────⊰◆⊱────────╮\n"   
        f" ➠ 𝐌𝐚𝐝𝐞 𝐁𝐲 : {CREDIT} 💻\n"
        f"╰────────⊰◆⊱────────╯\n"
    )
    
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["commands"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("upgrade_command"))
async def upgrade_button(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main_menu")]])
    caption = (
           f" 🎉 Welcome [{first_name}](tg://user?id={user_id}) to DRM Bot! 🎉\n\n"
           f"You can have access to download all Non-DRM+AES Encrypted URLs 🔐 including\n\n"
           f"<blockquote>• 📚 Appx Zip+Encrypted Url\n"
           f"• 🎓 Classplus DRM+ NDRM\n"
           f"• 🧑‍🏫 PhysicsWallah DRM\n"
           f"• 📚 CareerWill + PDF\n"
           f"• 🎓 Khan GS\n"
           f"• 🎓 Study Iq DRM\n"
           f"• 🚀 APPX + APPX Enc PDF\n"
           f"• 🎓 Vimeo Protection\n"
           f"• 🎓 Brightcove Protection\n"
           f"• 🎓 Visionias Protection\n"
           f"• 🎓 Zoom Video\n"
           f"• 🎓 Utkarsh Protection(Video + PDF)\n"
           f"• 🎓 All Non DRM+AES Encrypted URLs\n"
           f"• 🎓 MPD URLs if the key is known (e.g., Mpd_url?key=key XX:XX)</blockquote>\n\n"
           f"<b>💵 Monthly Plan: 100 INR</b>\n\n"
           f"If you want to buy membership of the bot, feel free to contact [{CREDIT}](tg://user?id={OWNER})\n"
    )  
    
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["upgrade"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("feat_command"))
async def feature_button(client, callback_query):
    caption = "**✨ My Premium BOT Features :**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Auto Pin Batch Name", callback_data="pin_command")],
        [InlineKeyboardButton("💧 Watermark", callback_data="watermark_command"), InlineKeyboardButton("🔄 Reset", callback_data="reset_command")],
        [InlineKeyboardButton("🖨️ Bot Working Logs", callback_data="logs_command")],
        [InlineKeyboardButton("🖋️ File Name", callback_data="custom_command"), InlineKeyboardButton("🏷️ Title", callback_data="titlle_command")],
        [InlineKeyboardButton("🎥 YouTube", callback_data="yt_command")],
        [InlineKeyboardButton("📝 Text File", callback_data="txt_maker_command"), InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_command")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("pin_command"))
async def pin_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**Auto Pin 📌 Batch Name :**\n\nAutomatically Pins the Batch Name in Channel or Group, If Starting from the First Link."
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )
    
@bot.on_callback_query(filters.regex("watermark_command"))
async def watermark_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**Custom Watermark :**\n\nSet Your Own Custom Watermark on Videos for Added Personalization."
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("reset_command"))
async def restart_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**🔄 Reset Command:**\n\nIf You Want to Reset or Restart Your Bot, Simply Use Command /reset."
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("logs_command"))
async def logs_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**🖨️ Bot Working Logs:**\n\n◆/logs - Bot Send Working Logs in .txt File."
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("custom_command"))
async def custom_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**🖋️ Custom File Name:**\n\nSupport for Custom Name before the File Extension.\nAdd name ..when txt is uploading"
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("titlle_command"))
async def titlle_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**Custom Title Feature :**\nAdd and customize titles at the starting\n**NOTE 📍 :** The Titile must enclosed within (Title), Best For appx's .txt file."
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("broadcast_command"))
async def broadcast_callback(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**📢 Broadcasting Support:**\n\n◆/broadcast - 📢 Broadcast to All Users.\n◆/broadusers - 👁️ To See All Broadcasting User"
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("txt_maker_command"))
async def editor_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**🤖 Available Commands 🗓️**\n◆/t2t for text to .txt file\n"
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["features"], caption=caption),
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("yt_command"))
async def y2t_button(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Feature", callback_data="feat_command")]])
    caption = f"**YouTube Commands:**\n\n◆/y2t - 🔪 YouTube Playlist → .txt Converter\n◆/ytm - 🎶 YouTube → .mp3 downloader\n\n<blockquote><b>◆YouTube → .mp3 downloader\n01. Send YouTube Playlist.txt file\n02. Send single or multiple YouTube links set\neg.\n`https://www.youtube.com/watch?v=xxxxxx\nhttps://www.youtube.com/watch?v=yyyyyy`</b></blockquote>"
    await callback_query.message.edit_media(
        InputMediaPhoto(media=PHOTO_URLS["youtube"], caption=caption),
        reply_markup=keyboard
        )
    @bot.on_message(filters.command(["id"]))
async def id_command(client: Client, message: Message):
    """Get chat/user ID."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Send to Owner", url=f"tg://openmessage?user_id={OWNER}")]
    ])
    chat_id = message.chat.id
    text = f"<blockquote expandable><b>The ID of this chat id is:</b></blockquote>\n`{chat_id}`"
    
    await message.reply_text(text, reply_markup=keyboard)

@bot.on_message(filters.private & filters.command(["info"]))
async def info_handler(client: Client, message: Message):
    """Get user information."""
    user = message.from_user
    text = (
        f"╭────────────────╮\n"
        f"│✨ **Your Telegram Info**✨ \n"
        f"├────────────────\n"
        f"├🔹**Name :** `{user.first_name} {user.last_name if user.last_name else 'None'}`\n"
        f"├🔹**User ID :** @{user.username if user.username else 'None'}\n"
        f"├🔹**TG ID :** `{user.id}`\n"
        f"├🔹**Profile :** {user.mention}\n"
        f"╰────────────────╯"
    )
    
    await message.reply_text(        
        text=text,
        disable_web_page_preview=True,
        reply_markup=BUTTONSCONTACT
    )

@bot.on_message(filters.command(["logs"]))
async def send_logs_handler(client: Client, message: Message):
    """Send bot logs."""
    try:
        if Path("bot.log").exists():
            sent = await message.reply_text("**📤 Sending you ....**")
            await message.reply_document(document="bot.log")
            await safe_delete_message(sent)
        else:
            await message.reply_text("**No logs found.**")
    except Exception as e:
        await message.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")

# Main DRM handler with improved error handling and resource management
@bot.on_message(filters.command(["drm"]))
async def drm_handler(client: Client, message: Message):
    """Main DRM download handler."""
    if bot_state.processing_request:
        await message.reply_text("**Another process is already running. Please wait.**")
        return
        
    bot_state.processing_request = True
    bot_state.cancel_requested = False
    
    try:
        if message.chat.id not in AUTH_USERS:
            await client.send_message(
                message.chat.id,
                f"<blockquote>__**Oopss! You are not a Premium member\nPLEASE /upgrade YOUR PLAN\nSend me your user id for authorization\nYour User id**__ - `{message.chat.id}`</blockquote>\n"
            )
            return

        editable = await message.reply_text(
            f"**__Hii, I am drm Downloader Bot__\n<blockquote><i>Send Me Your text file which enclude Name with url...\nE.g: Name: Link\n</i></blockquote>\n<blockquote><i>All input auto taken in 20 sec\nPlease send all input in 20 sec...\n</i></blockquote>**"
        )
        
        input_msg: Message = await client.listen(editable.chat.id, timeout=60)
        file_path = await input_msg.download()
        
        # Send file to owner for backup
        try:
            await client.send_document(OWNER, file_path)
        except Exception as e:
            logger.warning(f"Could not send file to owner: {e}")
            
        await safe_delete_message(input_msg)
        
        file_name = Path(file_path).stem
        path = f"./downloads/{message.chat.id}"
        Path(path).mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
            
            links, stats = await process_links_content(content)
            
            await editable.edit(
                f"**Total 🔗 links found are {stats['total_count']}\n"
                f"<blockquote>•PDF : {stats['pdf_count']}      •V2 : {stats['v2_count']}\n"
                f"•Img : {stats['img_count']}      •YT : {stats['yt_count']}\n"
                f"•zip : {stats['zip_count']}       •m3u8 : {stats['m3u8_count']}\n"
                f"•drm : {stats['drm_count']}      •Other : {stats['other_count']}\n"
                f"•mpd : {stats['mpd_count']}</blockquote>\n"
                f"Send From where you want to download**"
            )
            
            try:
                input_start: Message = await client.listen(editable.chat.id, timeout=20)
                raw_text = input_start.text
                await safe_delete_message(input_start)
            except asyncio.TimeoutError:
                raw_text = '1'
            
            start_index = validate_user_input(raw_text, len(links))
            
            if start_index > len(links):
                await editable.edit(f"**🔹Enter number in range of Index (01-{len(links)})**")
                return

            await editable.edit(f"**If You Want Set All Value Default then Send /d Otherwise Send /no**")
            try:
                input_all: Message = await client.listen(editable.chat.id, timeout=20)
                raw_text_all = input_all.text
                await safe_delete_message(input_all)
            except asyncio.TimeoutError:
                raw_text_all = '/d'
            
            # Process user inputs for configuration
            if raw_text_all == '/d':
                b_name = file_name.replace('_', ' ')
                raw_text2 = '480'
                res = "854x480"
                quality = f"{raw_text2}p"
                CR = f"{CREDIT}"
                thumb = '/d'
            else:
                await editable.edit(f"**Enter Batch Name or send /d**")
                try:
                    input1: Message = await client.listen(editable.chat.id, timeout=20)
                    raw_text0 = input1.text
                    await safe_delete_message(input1)
                except asyncio.TimeoutError:
                    raw_text0 = '/d'
              
                b_name = file_name.replace('_', ' ') if raw_text0 == '/d' else raw_text0
             
                await editable.edit("__**Enter resolution or Video Quality (`144`, `240`, `360`, `480`, `720`, `1080`)**__")
                try:
                    input2: Message = await client.listen(editable.chat.id, timeout=20)
                    raw_text2 = input2.text
                    await safe_delete_message(input2)
                except asyncio.TimeoutError:
                    raw_text2 = '480'
                    
                quality = f"{raw_text2}p"
                try:
                    if raw_text2 == "144":
                        res = "256x144"
                    elif raw_text2 == "240":
                        res = "426x240"
                    elif raw_text2 == "360":
                        res = "640x360"
                    elif raw_text2 == "480":
                        res = "854x480"
                    elif raw_text2 == "720":
                        res = "1280x720"
                    elif raw_text2 == "1080":
                        res = "1920x1080" 
                    else: 
                        res = "UN"
                except Exception:
                    res = "UN"

                await editable.edit(
                    f"**Enter the Credit Name or send /d\n\n<blockquote><b>Format:</b>\n"
                    f"🔹Send __Admin__ only for caption\n"
                    f"🔹Send __Admin,filename__ for caption and file...Separate them with a comma (,)</blockquote>**"
                )
                try:
                    input3: Message = await client.listen(editable.chat.id, timeout=20)
                    raw_text3 = input3.text
                    await safe_delete_message(input3)
                except asyncio.TimeoutError:
                    raw_text3 = '/d'
                
                if raw_text3 == '/d':
                    CR = f"{CREDIT}"
                elif "," in raw_text3:
                    CR, PRENAME = raw_text3.split(",")
                else:
                    CR = raw_text3
             
                await editable.edit(f"**Send the Video Thumb URL or send /d**")
                try:
                    input6: Message = await client.listen(editable.chat.id, timeout=20)
                    raw_text6 = input6.text
                    await safe_delete_message(input6)
                except asyncio.TimeoutError:
                    raw_text6 = '/d'

                if raw_text6.startswith("http://") or raw_text6.startswith("https://"):
                    # Download thumbnail from URL
                    success = await download_file_with_retry(raw_text6, 'thumb.jpg')
                    thumb = "thumb.jpg" if success else '/d'
                else:
                    thumb = raw_text6

            await editable.edit(
                "__**⚠️Provide the Channel ID or send /d__\n\n<blockquote><i>🔹 Make me an admin to upload.\n"
                "🔸Send /id in your channel to get the Channel ID.\n\n"
                "Example: Channel ID = -100XXXXXXXXXXX</i></blockquote>\n**"
            )
            try:
                input7: Message = await client.listen(editable.chat.id, timeout=20)
                raw_text7 = input7.text
                await safe_delete_message(input7)
            except asyncio.TimeoutError:
                raw_text7 = '/d'

            channel_id = message.chat.id if "/d" in raw_text7 else raw_text7    
            await safe_delete_message(editable)

            try:
                if start_index == 1:
                    batch_message = await client.send_message(
                        chat_id=channel_id, 
                        text=f"<blockquote><b>🎯Target Batch : {b_name}</b></blockquote>"
                    )
                    if "/d" not in raw_text7:
                        await client.send_message(
                            chat_id=message.chat.id,
                            text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n"
                                 f"🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩"
                        )
                        await client.pin_chat_message(channel_id, batch_message.id)
                        message_id = batch_message.id
                        pinning_message_id = message_id + 1
                        await client.delete_messages(channel_id, pinning_message_id)
                else:
                    if "/d" not in raw_text7:
                        await client.send_message(
                            chat_id=message.chat.id,
                            text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n"
                                 f"🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩"
                        )
            except Exception as e:
                await message.reply_text(
                    f"**Fail Reason »**\n<blockquote><i>{e}</i></blockquote>\n\n✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}🌟`"
                )

            # Start processing links
            failed_count = 0
            count = start_index
            
            for i in range(start_index - 1, len(links)):
                if bot_state.cancel_requested:
                    await message.reply_text("🚦**STOPPED**🚦")
                    break
                
                try:
                    Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
                    url = "https://" + Vxy
                    link0 = "https://" + Vxy

                    name1 = links[i][0].replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
                    
                    if "," in raw_text3:
                        name = f'{str(count).zfill(3)}) {PRENAME} {name1[:60]}'
                        namef = f'{PRENAME} {name1[:60]}'
                    else:
                        name = f'{str(count).zfill(3)}) {name1[:60]}'
                        namef = f'{name1[:60]}'
                    
                    # Process different URL types
                    if "visionias" in url:
                        async with ClientSession() as session:
                            async with session.get(url, headers={
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Cache-Control': 'no-cache',
                                'Connection': 'keep-alive',
                                'Pragma': 'no-cache',
                                'Referer': 'http://www.visionias.in/',
                                'Sec-Fetch-Dest': 'iframe',
                                'Sec-Fetch-Mode': 'navigate',
                                'Sec-Fetch-Site': 'cross-site',
                                'Upgrade-Insecure-Requests': '1',
                                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                                'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                                'sec-ch-ua-mobile': '?1',
                                'sec-ch-ua-platform': '"Android"',
                            }) as resp:
                                text = await resp.text()
                                url_match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                                if url_match:
                                    url = url_match.group(1)

                    if "acecwply" in url:
                        cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
             
                    elif "https://cpvod.testbook.com/" in url or "classplusapp.com/drm/" in url:
                        url = url.replace("https://cpvod.testbook.com/","https://media-cdn.classplusapp.com/drm/")
                        url = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                        mpd, keys = helper.get_mps_and_keys(url)
                        url = mpd
                        keys_string = " ".join([f"--key {key}" for key in keys])

                    elif "classplusapp" in url:
                        signed_api = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                        response = requests.get(signed_api, timeout=20)
                        if response.status_code == 200:
                            url = response.json().get('url', url)
                            
                    elif "tencdn.classplusapp" in url:
                        headers = {
                            'host': 'api.classplusapp.com',
                            'x-access-token': f'{bot_state.cptoken}',
                            'accept-language': 'EN',
                            'api-version': '18',
                            'app-version': '1.4.73.2',
                            'build-number': '35',
                            'connection': 'Keep-Alive',
                            'content-type': 'application/json',
                            'device-details': 'Xiaomi_Redmi 7_SDK-32',
                            'device-id': 'c28d3cb16bbdac01',
                            'region': 'IN',
                            'user-agent': 'Mobile-Android',
                            'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                            'accept-encoding': 'gzip'
                        }
                        params = {"url": f"{url}"}
                        response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                        if response.status_code == 200:
                            url = response.json().get('url', url)
                   
                    elif 'videos.classplusapp' in url:
                        response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{bot_state.cptoken}'})
                        if response.status_code == 200:
                            url = response.json().get('url', url)
                    
                    elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url: 
                        headers = {
                            'host': 'api.classplusapp.com',
                            'x-access-token': f'{bot_state.cptoken}',
                            'accept-language': 'EN',
                            'api-version': '18',
                            'app-version': '1.4.73.2',
                            'build-number': '35',
                            'connection': 'Keep-Alive',
                            'content-type': 'application/json',
                            'device-details': 'Xiaomi_Redmi 7_SDK-32',
                            'device-id': 'c28d3cb16bbdac01',
                            'region': 'IN',
                            'user-agent': 'Mobile-Android',
                            'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                            'accept-encoding': 'gzip'
                        }
                        params = {"url": f"{url}"}
                        response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                        if response.status_code == 200:
                            url = response.json().get('url', url)

                    if "edge.api.brightcove.com" in url:
                        bcov = f'bcov_auth={bot_state.cwtoken}'
                        url = url.split("bcov_auth")[0] + bcov

                    elif "childId" in url and "parentId" in url:
                        url = f"https://anonymouspwplayer-0e5a3f512dec.herokuapp.com/pw?url={url}&token={bot_state.pwtoken}"
                                       
                    if ".pdf*" in url:
                        url = f"https://dragoapi.vercel.app/pdf/{url}"
                    
                    elif 'encrypted.m' in url:
                        appxkey = url.split('*')[1]
                        url = url.split('*')[0]

                    # Set yt-dlp format based on URL type
                    if "youtu" in url:
                        ytf = f"bv*[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[height<=?{raw_text2}]"
                    elif "embed" in url:
                        ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
                    else:
                        ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
                   
                    # Set appropriate command based on URL type
                    if "jw-prod" in url:
                        cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
                    elif "webvideos.classplusapp." in url:
                       cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
                    elif "youtube.com" in url or "youtu.be" in url:
                        cmd = f'yt-dlp --cookies {bot_state.cookies_file_path} -f "{ytf}" "{url}" -o "{name}".mp4'
                    else:
                        cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'
                                    # Generate captions based on settings
                try:
                    if bot_state.caption == "/d":
                        if bot_state.topic == "yes":
                            raw_title = links[i][0]
                            t_match = re.search(r"[\(\[]([^\)\]]+)[\)\]]", raw_title)
                            if t_match:
                                t_name = t_match.group(1).strip()
                                v_name = re.sub(r"^[\(\[][^\)\]]+[\)\]]\s*", "", raw_title)
                                v_name = re.sub(r"[\(\[][^\)\]]+[\)\]]", "", v_name)
                                v_name = re.sub(r":.*", "", v_name).strip()
                            else:
                                t_name = "Untitled"
                                v_name = re.sub(r":.*", "", raw_title).strip()
                        
                            cc = f'[🎥]Vid Id : {str(count).zfill(3)}\n**Video Title :** `{v_name} [{res}p] .mkv`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            cc1 = f'[📕]Pdf Id : {str(count).zfill(3)}\n**File Title :** `{v_name} .pdf`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            cczip = f'[📁]Zip Id : {str(count).zfill(3)}\n**Zip Title :** `{v_name} .zip`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            ccimg = f'[🖼️]Img Id : {str(count).zfill(3)}\n**Img Title :** `{v_name} .jpg`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            cchtml = f'[🌐]Html Id : {str(count).zfill(3)}\n**Html Title :** `{v_name} .html`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            ccyt = f'[🎥]Vid Id : {str(count).zfill(3)}\n**Video Title :** `{v_name} .mp4`\n<a href="{url}">__**Click Here to Watch Stream**__</a>\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                            ccm = f'[🎵]Mp3 Id : {str(count).zfill(3)}\n**Audio Title :** `{v_name} .mp3`\n<blockquote><b>Batch Name : {b_name}\nTopic Name : {t_name}</b></blockquote>\n\n**Extracted by➤**{CR}\n'
                        else:
                            cc = f'[🎥]Vid Id : {str(count).zfill(3)}\n**Video Title :** `{name1} [{res}p] .mkv`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
                            cc1 = f'[📕]Pdf Id : {str(count).zfill(3)}\n**File Title :** `{name1} .pdf`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
                            cczip = f'[📁]Zip Id : {str(count).zfill(3)}\n**Zip Title :** `{name1} .zip`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n' 
                            ccimg = f'[🖼️]Img Id : {str(count).zfill(3)}\n**Img Title :** `{name1} .jpg`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
                            ccm = f'[🎵]Audio Id : {str(count).zfill(3)}\n**Audio Title :** `{name1} .mp3`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
                            cchtml = f'[🌐]Html Id : {str(count).zfill(3)}\n**Html Title :** `{name1} .html`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
                    else:
                        cc = f'**{str(count).zfill(3)}) {name1} [{res}p] .mkv**'
                        cc1 = f'**{str(count).zfill(3)}) {name1} .pdf**'
                        cczip = f'**{str(count).zfill(3)}) {name1} .zip**'
                        ccimg = f'**{str(count).zfill(3)}) {name1} .jpg**'
                        ccm = f'**{str(count).zfill(3)}) {name1} .mp3**'
                        cc1html = f'**{str(count).zfill(3)}) {name1} .html**'
                    
                    # Handle different file types
                    if "drive" in url:
                        try:
                            ka = await helper.download(url, name)
                            copy = await client.send_document(chat_id=channel_id, document=ka, caption=cc1)
                            count += 1
                            await safe_remove_file(ka)
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            await asyncio.sleep(e.x)
                            continue    
  
                    elif ".pdf" in url:
                        if "cwmediabkt99" in url:
                            max_retries = 15
                            retry_delay = 4
                            success = False
                            failure_msgs = []
                            
                            for attempt in range(max_retries):
                                try:
                                    await asyncio.sleep(retry_delay)
                                    url_encoded = url.replace(" ", "%20")
                                    scraper = cloudscraper.create_scraper()
                                    response = scraper.get(url_encoded)

                                    if response.status_code == 200:
                                        async with aiofiles.open(f'{namef}.pdf', 'wb') as file:
                                            await file.write(response.content)
                                        await asyncio.sleep(retry_delay)
                                        copy = await client.send_document(chat_id=channel_id, document=f'{namef}.pdf', caption=cc1)
                                        count += 1
                                        await safe_remove_file(f'{namef}.pdf')
                                        success = True
                                        break
                                    else:
                                        failure_msg = await message.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                        failure_msgs.append(failure_msg)
                                        
                                except Exception as e:
                                    failure_msg = await message.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                                    failure_msgs.append(failure_msg)
                                    await asyncio.sleep(retry_delay)
                                    continue
                                    
                            for msg in failure_msgs:
                                await safe_delete_message(msg)
                                
                        else:
                            try:
                                cmd_pdf = f'yt-dlp -o "{namef}.pdf" "{url}"'
                                download_cmd = f"{cmd_pdf} -R 25 --fragment-retries 25"
                                success, output = await execute_command_async(download_cmd)
                                if success and Path(f'{namef}.pdf').exists():
                                    copy = await client.send_document(chat_id=channel_id, document=f'{namef}.pdf', caption=cc1)
                                    count += 1
                                else:
                                    raise Exception(f"PDF download failed: {output}")
                            except FloodWait as e:
                                await message.reply_text(str(e))
                                await asyncio.sleep(e.x)
                                continue
                            finally:
                                await safe_remove_file(f'{namef}.pdf')

                    elif ".ws" in url and url.endswith(".ws"):
                        try:
                            await helper.pdf_download(f"{bot_state.api_url}utkash-ws?url={url}&authorization={bot_state.api_token}", f"{name}.html")
                            await asyncio.sleep(1)
                            await client.send_document(chat_id=channel_id, document=f"{name}.html", caption=cchtml)
                            await safe_remove_file(f'{name}.html')
                            count += 1
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            await asyncio.sleep(e.x)
                            continue    
                                
                    elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            ext = url.split('.')[-1]
                            cmd_img = f'yt-dlp -o "{namef}.{ext}" "{url}"'
                            download_cmd = f"{cmd_img} -R 25 --fragment-retries 25"
                            success, output = await execute_command_async(download_cmd)
                            if success and Path(f'{namef}.{ext}').exists():
                                copy = await client.send_photo(chat_id=channel_id, photo=f'{namef}.{ext}', caption=ccimg)
                                count += 1
                            else:
                                raise Exception(f"Image download failed: {output}")
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            await asyncio.sleep(e.x)
                            continue
                        finally:
                            await safe_remove_file(f'{namef}.{ext}')

                    elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                        try:
                            ext = url.split('.')[-1]
                            cmd_audio = f'yt-dlp -o "{namef}.{ext}" "{url}"'
                            download_cmd = f"{cmd_audio} -R 25 --fragment-retries 25"
                            success, output = await execute_command_async(download_cmd)
                            if success and Path(f'{namef}.{ext}').exists():
                                copy = await client.send_document(chat_id=channel_id, document=f'{namef}.{ext}', caption=ccm)
                                count += 1
                            else:
                                raise Exception(f"Audio download failed: {output}")
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            await asyncio.sleep(e.x)
                            continue
                        finally:
                            await safe_remove_file(f'{namef}.{ext}')
                        
                    elif 'encrypted.m' in url:    
                        remaining_links = len(links) - count
                        progress = (count / len(links)) * 100
                        Show1 = f"<blockquote>🚀𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 » {progress:.2f}%</blockquote>\n┃\n" \
                               f"┣🔗𝐈𝐧𝐝𝐞𝐱 » {count}/{len(links)}\n┃\n" \
                               f"╰━🖇️𝐑𝐞𝐦𝐚𝐢𝐧 » {remaining_links}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote><b>⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Eɴᴄʀʏᴘᴛᴇᴅ Sᴛᴀʀᴛᴇᴅ...⏳</b></blockquote>\n┃\n" \
                               f'┣💃𝐂𝐫𝐞𝐝𝐢𝐭 » {CR}\n┃\n' \
                               f"╰━📚𝐁𝐚𝐭𝐜𝐡 » {b_name}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote>📚𝐓𝐢𝐭𝐥𝐞 » {namef}</blockquote>\n┃\n" \
                               f"┣🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {quality}\n┃\n" \
                               f'┣━🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">**Original Link**</a>\n┃\n' \
                               f'╰━━🖇️𝐔𝐫𝐥 » <a href="{url}">**Api Link**</a>\n' \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"🛑**Send** /stop **to stop process**\n┃\n" \
                               f"╰━✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                        Show = f"<i><b>Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>" 
                        prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)
                        prog1 = await message.reply_text(Show1, disable_web_page_preview=True)
                        res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)  
                        filename = res_file  
                        await safe_delete_message(prog1)
                        await safe_delete_message(prog)
                        await helper.send_vid(client, message, cc, filename, bot_state.vidwatermark, thumb, name, prog, channel_id)
                        count += 1  
                        await asyncio.sleep(1)  
                        continue  

                    elif 'drmcdni' in url or 'drm/wv' in url or 'drm/common' in url:
                        remaining_links = len(links) - count
                        progress = (count / len(links)) * 100
                        Show1 = f"<blockquote>🚀𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 » {progress:.2f}%</blockquote>\n┃\n" \
                               f"┣🔗𝐈𝐧𝐝𝐞𝐱 » {count}/{len(links)}\n┃\n" \
                               f"╰━🖇️𝐑𝐞𝐦𝐚𝐢𝐧 » {remaining_links}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote><b>⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳</b></blockquote>\n┃\n" \
                               f'┣💃𝐂𝐫𝐞𝐝𝐢𝐭 » {CR}\n┃\n' \
                               f"╰━📚𝐁𝐚𝐭𝐜𝐡 » {b_name}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote>📚𝐓𝐢𝐭𝐥𝐞 » {namef}</blockquote>\n┃\n" \
                               f"┣🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {quality}\n┃\n" \
                               f'┣━🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">**Original Link**</a>\n┃\n' \
                               f'╰━━🖇️𝐔𝐫𝐥 » <a href="{url}">**Api Link**</a>\n' \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"🛑**Send** /stop **to stop process**\n┃\n" \
                               f"╰━✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                        Show = f"<i><b>Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                        prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)
                        prog1 = await message.reply_text(Show1, disable_web_page_preview=True)
                        res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                        filename = res_file
                        await safe_delete_message(prog1)
                        await safe_delete_message(prog)
                        await helper.send_vid(client, message, cc, filename, bot_state.vidwatermark, thumb, name, prog, channel_id)
                        count += 1
                        await asyncio.sleep(1)
                        continue
     
                    else:
                        remaining_links = len(links) - count
                        progress = (count / len(links)) * 100
                        Show1 = f"<blockquote>🚀𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 » {progress:.2f}%</blockquote>\n┃\n" \
                               f"┣🔗𝐈𝐧𝐝𝐞𝐱 » {count}/{len(links)}\n┃\n" \
                               f"╰━🖇️𝐑𝐞𝐦𝐚𝐢𝐧 » {remaining_links}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote><b>⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳</b></blockquote>\n┃\n" \
                               f'┣💃𝐂𝐫𝐞𝐝𝐢𝐭 » {CR}\n┃\n' \
                               f"╰━📚𝐁𝐚𝐭𝐜𝐡 » {b_name}\n" \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"<blockquote>📚𝐓𝐢𝐭𝐥𝐞 » {namef}</blockquote>\n┃\n" \
                               f"┣🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {quality}\n┃\n" \
                               f'┣━🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">**Original Link**</a>\n┃\n' \
                               f'╰━━🖇️𝐔𝐫𝐥 » <a href="{url}">**Api Link**</a>\n' \
                               f"━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                               f"🛑**Send** /stop **to stop process**\n┃\n" \
                               f"╰━✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                        Show = f"<i><b>Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                        prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)
                        prog1 = await message.reply_text(Show1, disable_web_page_preview=True)
                        res_file = await helper.download_video(url, cmd, name)
                        filename = res_file
                        await safe_delete_message(prog1)
                        await safe_delete_message(prog)
                        await helper.send_vid(client, message, cc, filename, bot_state.vidwatermark, thumb, name, prog, channel_id)
                        count += 1
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    await client.send_message(
                        channel_id, 
                        f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', 
                        disable_web_page_preview=True
                    )
                    count += 1
                    failed_count += 1
                    continue

    except Exception as e:
        await message.reply_text(f"Error processing file: {str(e)}")
        logger.error(f"DRM handler error: {e}")
    finally:
        await safe_remove_file(file_path)

except Exception as e:
    logger.error(f"DRM handler main error: {e}")
    await message.reply_text(f"**Error in DRM handler:**\n<blockquote>{str(e)}</blockquote>")
finally:
    bot_state.processing_request = False
    bot_state.cancel_requested = False

    # Send completion message
    success_count = len(links) - failed_count
    video_count = (stats['v2_count'] + stats['mpd_count'] + stats['m3u8_count'] + 
                  stats['yt_count'] + stats['drm_count'] + stats['zip_count'] + stats['other_count'])
    
    completion_msg = (
        f"<b>-┈━═.•°✅ Completed ✅°•.═━┈-</b>\n"
        f"<blockquote><b>🎯Batch Name : {b_name}</b></blockquote>\n"
        f"<blockquote>🔗 Total URLs: {len(links)} \n"
        f"┃   ┠🔴 Total Failed URLs: {failed_count}\n"
        f"┃   ┠🟢 Total Successful URLs: {success_count}\n"
        f"┃   ┃   ┠🎥 Total Video URLs: {video_count}\n"
        f"┃   ┃   ┠📄 Total PDF URLs: {stats['pdf_count']}\n"
        f"┃   ┃   ┠📸 Total IMAGE URLs: {stats['img_count']}</blockquote>\n"
    )
    
    if raw_text7 == "/d":
        await client.send_message(channel_id, completion_msg)
    else:
        await client.send_message(channel_id, completion_msg)
        await client.send_message(message.chat.id, f"<blockquote><b>✅ Your Task is completed, please check your Set Channel📱</b></blockquote>")
    # Text handler for direct links
@bot.on_message(filters.text & filters.private)
async def text_handler(client: Client, message: Message):
    """Handle direct text links."""
    if message.from_user.is_bot:
        return
        
    links = message.text
    match = re.search(r'https?://\S+', links)
    if match:
        link = match.group(0)
    else:
        return
        
    editable = await message.reply_text(f"<pre><code>**🔹Processing your link...\n🔁Please wait...⏳**</code></pre>")
    await safe_delete_message(message)

    if ".pdf" in link or ".jpeg" in link or ".jpg" in link or ".png" in link:
        await safe_delete_message(editable)
        raw_text2 = "360"
        quality = "360p"
        res = "640x360"
    else:
        await editable.edit(
            f"╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ \n"
            f"┣━━⪼ send `144`  for 144p\n"
            f"┣━━⪼ send `240`  for 240p\n"
            f"┣━━⪼ send `360`  for 360p\n"
            f"┣━━⪼ send `480`  for 480p\n"
            f"┣━━⪼ send `720`  for 720p\n"
            f"┣━━⪼ send `1080` for 1080p\n"
            f"╰━━⌈⚡[🦋`{CREDIT}`🦋]⚡⌋━━➣ "
        )
        input2: Message = await client.listen(message.chat.id, filters=filters.text & filters.user(message.from_user.id), timeout=30)
        raw_text2 = input2.text
        quality = f"{raw_text2}p"
        await safe_delete_message(input2)
        try:
            if raw_text2 == "144":
                res = "256x144"
            elif raw_text2 == "240":
                res = "426x240"
            elif raw_text2 == "360":
                res = "640x360"
            elif raw_text2 == "480":
                res = "854x480"
            elif raw_text2 == "720":
                res = "1280x720"
            elif raw_text2 == "1080":
                res = "1920x1080" 
            else: 
                res = "UN"
        except Exception:
            res = "UN"
          
        await safe_delete_message(editable)

    vidwatermark = "/d"
    raw_text4 = "working_token"
    thumb = "/d"
    count = 0
    arg = 1
    channel_id = message.chat.id
    
    try:
        Vxy = link.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
        url = Vxy

        if "youtu" in url:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            response = requests.get(oembed_url)
            audio_title = response.json().get('title', 'YouTube Video')
            audio_title = audio_title.replace("_", " ")
            name = f'{audio_title[:60]}'        
            name1 = f'{audio_title}'
        else:
            name1 = links.replace("(", "[").replace(")", "]").replace("_", " ").replace("\t", "").replace(":", " ").replace("/", " ").replace("+", " ").replace("#", " ").replace("|", " ").replace("@", " ").replace("*", " ").replace(".", " ").replace("https", "").replace("http", "").strip()
            name = f'{name1[:60]}'
        
        if "visionias" in url:
            async with ClientSession() as session:
                async with session.get(url, headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Referer': 'http://www.visionias.in/',
                    'Sec-Fetch-Dest': 'iframe',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                    'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                }) as resp:
                    text = await resp.text()
                    url_match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                    if url_match:
                        url = url_match.group(1)

        if "acecwply" in url:
            cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'

        elif "https://cpvod.testbook.com/" in url or "classplusapp.com/drm/" in url:
            url = url.replace("https://cpvod.testbook.com/","https://media-cdn.classplusapp.com/drm/")
            url = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
            mpd, keys = helper.get_mps_and_keys(url)
            url = mpd
            keys_string = " ".join([f"--key {key}" for key in keys])

        elif "classplusapp" in url:
            signed_api = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id={message.from_user.id}"
            response = requests.get(signed_api, timeout=20)
            if response.status_code == 200:
                url = response.json().get('url', url)

        elif "tencdn.classplusapp" in url:
            headers = {
                'host': 'api.classplusapp.com',
                'x-access-token': f'{raw_text4}',
                'accept-language': 'EN',
                'api-version': '18',
                'app-version': '1.4.73.2',
                'build-number': '35',
                'connection': 'Keep-Alive',
                'content-type': 'application/json',
                'device-details': 'Xiaomi_Redmi 7_SDK-32',
                'device-id': 'c28d3cb16bbdac01',
                'region': 'IN',
                'user-agent': 'Mobile-Android',
                'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                'accept-encoding': 'gzip'
            }
            params = {"url": f"{url}"}
            response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
            if response.status_code == 200:
                url = response.json().get('url', url)
       
        elif 'videos.classplusapp' in url:
            response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{raw_text4}'})
            if response.status_code == 200:
                url = response.json().get('url', url)
        
        elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url: 
            headers = {
                'host': 'api.classplusapp.com',
                'x-access-token': f'{raw_text4}',
                'accept-language': 'EN',
                'api-version': '18',
                'app-version': '1.4.73.2',
                'build-number': '35',
                'connection': 'Keep-Alive',
                'content-type': 'application/json',
                'device-details': 'Xiaomi_Redmi 7_SDK-32',
                'device-id': 'c28d3cb16bbdac01',
                'region': 'IN',
                'user-agent': 'Mobile-Android',
                'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                'accept-encoding': 'gzip'
            }
            params = {"url": f"{url}"}
            response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
            if response.status_code == 200:
                url = response.json().get('url', url)

        elif "childId" in url and "parentId" in url:
            url = f"https://pwplayer-38c1ae95b681.herokuapp.com/pw?url={url}&token={raw_text4}"
                       
        elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
            vid_id = url.split('/')[-2]
            url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"
            
        if ".pdf*" in url:
            url = f"https://dragoapi.vercel.app/pdf/{url}"
        
        elif 'encrypted.m' in url:
            appxkey = url.split('*')[1]
            url = url.split('*')[0]

        # Set yt-dlp format based on URL type
        if "youtu" in url:
            ytf = f"bv*[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[height<=?{raw_text2}]"
        elif "embed" in url:
            ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
        else:
            ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
       
        # Set appropriate command based on URL type
        if "jw-prod" in url:
            cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
        elif "webvideos.classplusapp." in url:
           cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
        elif "youtube.com" in url or "youtu.be" in url:
            cmd = f'yt-dlp --cookies {bot_state.cookies_file_path} -f "{ytf}" "{url}" -o "{name}".mp4'
        else:
            cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

        try:
            cc = f'🎞️ `{name} [{res}].mp4`\n<blockquote expandable>🔗𝐋𝐢𝐧𝐤 » {link}</blockquote>\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CREDIT}'
            cc1 = f'📕 `{name}`\n<blockquote expandable>🔗𝐋𝐢𝐧𝐤 » [Click Here to Open]({link})</blockquote>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CREDIT}'
              
            if "drive" in url:
                try:
                    ka = await helper.download(url, name)
                    copy = await client.send_document(chat_id=message.chat.id, document=ka, caption=cc1)
                    count += 1
                    await safe_remove_file(ka)
                except FloodWait as e:
                    await message.reply_text(str(e))
                    await asyncio.sleep(e.x)
                    pass

            elif ".pdf" in url:
                if "cwmediabkt99" in url:
                    max_retries = 15
                    retry_delay = 4
                    success = False
                    failure_msgs = []
                    
                    for attempt in range(max_retries):
                        try:
                            await asyncio.sleep(retry_delay)
                            url_encoded = url.replace(" ", "%20")
                            scraper = cloudscraper.create_scraper()
                            response = scraper.get(url_encoded)

                            if response.status_code == 200:
                                async with aiofiles.open(f'{name}.pdf', 'wb') as file:
                                    await file.write(response.content)
                                await asyncio.sleep(retry_delay)
                                copy = await client.send_document(chat_id=message.chat.id, document=f'{name}.pdf', caption=cc1)
                                await safe_remove_file(f'{name}.pdf')
                                success = True
                                break
                            else:
                                failure_msg = await message.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                failure_msgs.append(failure_msg)
                                
                        except Exception as e:
                            failure_msg = await message.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                            failure_msgs.append(failure_msg)
                            await asyncio.sleep(retry_delay)
                            continue

                    for msg in failure_msgs:
                        await safe_delete_message(msg)
                        
                    if not success:
                        await message.reply_text(
                            f"Failed to download PDF after {max_retries} attempts.\n⚠️**Downloading Failed**⚠️\n**Name** =>> {str(count).zfill(3)} {name1}\n**Url** =>> {link}",
                            disable_web_page_preview=True
                        )
                        
                else:
                    try:
                        cmd_pdf = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd_pdf} -R 25 --fragment-retries 25"
                        success, output = await execute_command_async(download_cmd)
                        if success and Path(f'{name}.pdf').exists():
                            copy = await client.send_document(chat_id=message.chat.id, document=f'{name}.pdf', caption=cc1)
                        else:
                            raise Exception(f"PDF download failed: {output}")
                    except FloodWait as e:
                        await message.reply_text(str(e))
                        await asyncio.sleep(e.x)
                        pass
                    finally:
                        await safe_remove_file(f'{name}.pdf')

            elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                try:
                    ext = url.split('.')[-1]
                    cmd_audio = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd_audio} -R 25 --fragment-retries 25"
                    success, output = await execute_command_async(download_cmd)
                    if success and Path(f'{name}.{ext}').exists():
                        await client.send_document(chat_id=message.chat.id, document=f'{name}.{ext}', caption=cc1)
                    else:
                        raise Exception(f"Audio download failed: {output}")
                except FloodWait as e:
                    await message.reply_text(str(e))
                    await asyncio.sleep(e.x)
                    pass
                finally:
                    await safe_remove_file(f'{name}.{ext}')

            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                try:
                    ext = url.split('.')[-1]
                    cmd_img = f'yt-dlp -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd_img} -R 25 --fragment-retries 25"
                    success, output = await execute_command_async(download_cmd)
                    if success and Path(f'{name}.{ext}').exists():
                        copy = await client.send_photo(chat_id=message.chat.id, photo=f'{name}.{ext}', caption=cc1)
                        count += 1
                    else:
                        raise Exception(f"Image download failed: {output}")
                except FloodWait as e:
                    await message.reply_text(str(e))
                    await asyncio.sleep(e.x)
                    pass
                finally:
                    await safe_remove_file(f'{name}.{ext}')
                                
            elif 'encrypted.m' in url:    
                Show = (
                    f"**⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳**\n"
                    f"<blockquote expandable>🔗𝐋𝐢𝐧𝐤 » {url}</blockquote>\n"
                    f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                )
                prog = await message.reply_text(Show, disable_web_page_preview=True)
                res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)  
                filename = res_file  
                await safe_delete_message(prog)  
                await helper.send_vid(client, message, cc, filename, vidwatermark, thumb, name, prog, channel_id)
                await asyncio.sleep(1)  
                pass

            elif 'drmcdni' in url or 'drm/wv' in url:
                Show = (
                    f"**⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳**\n"
                    f"<blockquote expandable>🔗𝐋𝐢𝐧𝐤 » {url}</blockquote>\n"
                    f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                )
                prog = await message.reply_text(Show, disable_web_page_preview=True)
                res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                filename = res_file
                await safe_delete_message(prog)
                await helper.send_vid(client, message, cc, filename, vidwatermark, thumb, name, prog, channel_id)
                await asyncio.sleep(1)
                pass
     
            else:
                Show = (
                    f"**⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳**\n"
                    f"<blockquote expandable>🔗𝐋𝐢𝐧𝐤 » {url}</blockquote>\n"
                    f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                )
                prog = await message.reply_text(Show, disable_web_page_preview=True)
                res_file = await helper.download_video(url, cmd, name)
                filename = res_file
                await safe_delete_message(prog)
                await helper.send_vid(client, message, cc, filename, vidwatermark, thumb, name, prog, channel_id)
                await asyncio.sleep(1)

        except Exception as e:
            await message.reply_text(
                f"⚠️𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n\n🔗𝐋𝐢𝐧𝐤 » `{link}`\n\n<blockquote><b><i>⚠️Failed Reason »\n{str(e)}</i></b></blockquote>"
            )
            pass

    except Exception as e:
        await message.reply_text(str(e))

# Bot startup functions
def notify_owner():
    """Notify owner when bot starts."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": OWNER,
            "text": "𝐁𝐨𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 ✅"
        }
        requests.post(url, data=data, timeout=10)
        logger.info("Owner notified about bot restart")
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")

def reset_and_set_commands():
    """Reset and set bot commands."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
        
        commands = [
            {"command": "start", "description": "✅ Check Alive the Bot"},
            {"command": "stop", "description": "🚫 Stop the ongoing process"},
            {"command": "broadcast", "description": "📢 Broadcast to All Users"},
            {"command": "broadusers", "description": "👨‍❤️‍👨 All Broadcasting Users"},
            {"command": "drm", "description": "📑 Upload .txt file"},
            {"command": "cookies", "description": "📁 Upload YT Cookies"},
            {"command": "caption", "description": "🖊️ Change Caption Style"},
            {"command": "topic", "description": "🎩 Topic Wise Uploading"},
            {"command": "vidwatermark", "description": "💦 Change Video Watermark"},
            {"command": "token", "description": "🖋️ Update CP/CW/PW Token"},
            {"command": "y2t", "description": "🔪 YouTube → .txt Converter"},
            {"command": "ytm", "description": "🎶 YouTube → .mp3 downloader"},
            {"command": "t2t", "description": "📟 Text → .txt Generator"},
            {"command": "reset", "description": "✅ Reset the Bot"},
            {"command": "id", "description": "🆔 Get Your ID"},
            {"command": "info", "description": "ℹ️ Check Your Information"},
            {"command": "logs", "description": "👁️ View Bot Activity"},
            {"command": "addauth", "description": "▶️ Add Authorisation"},
            {"command": "rmauth", "description": "⏸️ Remove Authorisation "},
            {"command": "users", "description": "👨‍👨‍👧‍👦 All Premium Users"}
        ]
        
        requests.post(url, json={"commands": commands}, timeout=10)
        logger.info("Bot commands set successfully")
        
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")

if __name__ == "__main__":
    logger.info("Starting bot...")
    reset_and_set_commands()
    notify_owner()

    try:
        bot.run()
        logger.info("Bot started successfully")
     except Exception as e:
         logger.error(f"Bot crashed: {e}")
        # Notify owner about crash
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": OWNER,
                "text": f"𝐁𝐨𝐭 𝐂𝐫𝐚𝐬𝐡𝐞𝐝 ❌\nError: {str(e)}"
            }
            requests.post(url, data=data, timeout=10)
        except Exception as notify_error:
            logger.error(f"Failed to notify owner about crash: {notify_error}")
```
        
