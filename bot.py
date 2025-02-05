import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

try:
    bot.load_extension('twitter_tracker')
except Exception as e:
    print(f"Failed to load extension: {e}")

bot.run(os.getenv('DISCORD_TOKEN'))
