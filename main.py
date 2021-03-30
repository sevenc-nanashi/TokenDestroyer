import base64
import os
import re
import textwrap

import aiohttp
import discord
from replit import db


client = discord.Client()
TOKEN_PATTERN = re.compile(r"([0-9a-zA-Z\-_]{24})\.[0-9a-zA-Z\-_]{6}\.[0-9a-zA-Z\-_]{27}")
token_cache = []

async def update_status():
    await client.change_presence(activity=discord.Game("Destroyed " + db["count"] + " Tokens"))

async def destroy_token(message, user, token):
    async with aiohttp.ClientSession() as session:
        if token not in token_cache:
            token_cache.append(token)
            db["count"] = str(int(db["count"]) + 1)
            token_text = textwrap.dedent(f"""
                {user}'s token has been leaked!
                {token}
                
                Guild:
                    {message.guild}
                
                Channel:
                    {message.channel}
                
                User:
                    {message.author}
                
                URL:
                    {message.jump_url}
                
                Make sure your token isn't public.
                
                (c)TokenDestroyer - 2021 sevenc-nanashi
                """)
            token_text_ja = textwrap.dedent(f"""
                {user}のトークンが漏れてしまいました！
                {token}
                
                サーバー：
                    {message.guild.name}
                
                チャンネル：
                    {message.channel.name}
                
                ユーザー：
                    {message.author}
                
                URL：
                    {message.jump_url}
                
                トークンが公開されていないか確かめて下さい。
                
                (c)TokenDestroyer - 2021 sevenc-nanashi
                """)
            async with session.post('https://api.github.com/gists', headers={"authorization": "token " + os.getenv("github_token")}, json={"files":{"token_en.txt": {"content":token_text}, "token_ja.txt": {"content":token_text_ja}}, "public": True}) as gist_response:
                if gist_response.status == 201:
                    await message.reply(f"**{user}'s token has been leaked!**\nToken has been disabled because we've uploaded token to gist, but please don't leak token more!\n\n**{user}のトークン漏れを検知しました！**\nGistにアップロードしたためトークンは無効化されましたが、公開しないように気をつけて下さい！")
                    await update_status()

@client.event
async def on_ready():
    print("Ready!")
    await update_status()

@client.event
async def on_message(message):
    for t in TOKEN_PATTERN.finditer(message.content):
        u = int(base64.urlsafe_b64decode(t[1]))
        try:
            user = await client.fetch_user(u)
        except discord.errors.NotFound:
            pass
        else:
            await destroy_token(message, user, t[0])
    
    for a in message.attachments:
        for t in TOKEN_PATTERN.finditer(str(await a.read())):
            u = int(base64.urlsafe_b64decode(t[1]))
            try:
                user = await client.fetch_user(u)
            except discord.errors.NotFound:
                pass
            else:
                await destroy_token(message, user, t[0])

                
client.run(os.getenv("token"))