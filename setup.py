from setuptools import setup, find_packages

setup(
    name="telegram-bot",
    version="1.0.0",
    description="A Telegram bot",
    packages=find_packages(),
    install_requires=[
        "telethon",
        "pyrogram",
        "tgcrypto",
        "aiohttp",
        "youtube-dl",
        "yt-dlp",
        "requests",
        "pillow"
    ],
    python_requires=">=3.7",
)
