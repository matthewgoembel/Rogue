import discord
from discord.ext import commands, tasks
import tweepy
import os
import asyncio
from datetime import datetime, timezone
import json

class TwitterTracker(commands.Cog):
    def __init__(self, bot, twitter_api, config):
        self.bot = bot
        self.twitter_api = twitter_api
        self.config = config
        self.last_tweets = {}
        self.check_tweets.start()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'twitter_accounts': [],
                'discord_channel_id': None
            }

    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    @tasks.loop(minutes=2)  # Check every 2 minutes
    async def check_tweets(self):
        channel = self.bot.get_channel(self.config['discord_channel_id'])
        if not channel:
            return

        for username in self.config['twitter_accounts']:
            try:
                # Get user's tweets
                tweets = self.twitter_api.user_timeline(
                    screen_name=username,
                    count=1,
                    tweet_mode="extended"
                )
                
                if not tweets:
                    continue

                latest_tweet = tweets[0]
                
                # Check if we've seen this tweet before
                if username in self.last_tweets:
                    if self.last_tweets[username] >= latest_tweet.id:
                        continue

                # Update last seen tweet
                self.last_tweets[username] = latest_tweet.id

                # Create embed
                embed = discord.Embed(
                    description=latest_tweet.full_text,
                    color=discord.Color.blue(),
                    timestamp=latest_tweet.created_at
                )
                embed.set_author(
                    name=f"@{username}",
                    url=f"https://twitter.com/{username}",
                    icon_url=latest_tweet.user.profile_image_url
                )

                # Add media if present
                if 'media' in latest_tweet.entities:
                    embed.set_image(url=latest_tweet.entities['media'][0]['media_url'])

                await channel.send(embed=embed)

            except Exception as e:
                print(f"Error processing tweets for {username}: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_twitter(self, ctx, username: str):
        """Add a Twitter account to track"""
        if username not in self.config['twitter_accounts']:
            self.config['twitter_accounts'].append(username)
            self.save_config()
            await ctx.send(f"Now tracking @{username}")
        else:
            await ctx.send(f"Already tracking @{username}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_twitter(self, ctx, username: str):
        """Remove a Twitter account from tracking"""
        if username in self.config['twitter_accounts']:
            self.config['twitter_accounts'].remove(username)
            self.save_config()
            await ctx.send(f"Stopped tracking @{username}")
        else:
            await ctx.send(f"Not tracking @{username}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def list_twitter(self, ctx):
        """List all tracked Twitter accounts"""
        if not self.config['twitter_accounts']:
            await ctx.send("No Twitter accounts are being tracked.")
            return
        accounts = "\n".join(f"@{username}" for username in self.config['twitter_accounts'])
        await ctx.send(f"Currently tracking:\n{accounts}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for Twitter updates"""
        self.config['discord_channel_id'] = channel.id
        self.save_config()
        await ctx.send(f"Twitter updates will be sent to {channel.mention}")

def setup(bot):
    # Load environment variables
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    # Set up Twitter API
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    twitter_api = tweepy.API(auth)

    # Load config
    config = TwitterTracker.load_config(None)
    
    bot.add_cog(TwitterTracker(bot, twitter_api, config))
    