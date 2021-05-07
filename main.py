import asyncio
import base64
import os
import re
import textwrap

import aiohttp
import discord
from replit import db


client = discord.Client(allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False))
TOKEN_PATTERN = re.compile(r"([0-9a-zA-Z\-_]{24})\.[0-9a-zA-Z\-_]{6,7}\.[0-9a-zA-Z\-_]{27}")
token_cache = []

async def ignore_forbidden(coro):
    try:
        return await coro
    except discord.errors.Forbidden:
        return None

async def update_status():
    await client.change_presence(activity=discord.Game(f'Destroyed {db["count"]} Tokens'))

async def destroy_token(message, user, token):
    if token not in token_cache:
        token_cache.append(token)
        db["count"] += 1
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
            This Gist will be deleted in 5 minutes.

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
            
            トークンが見える状況ではないか確かめて下さい。
            このGistは5分で削除されます。

            (c)TokenDestroyer - 2021 sevenc-nanashi
            """)
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.github.com/gists', headers={"authorization": "token " + os.getenv("github_token"), "accept": "application/json"}, json={"files":{"token_en.txt": {"content":token_text}, "token_ja.txt": {"content":token_text_ja}}, "public": True}) as gist_response:
                if gist_response.status == 201:
                    await ignore_forbidden(message.reply(f"**{user}'s token has been leaked!**\nToken has been disabled because we've uploaded token to gist, but please don't leak token more!\n\n**{user}のトークン漏れを検知しました！**\nGistにアップロードしたためトークンは無効化されましたが、公開しないように気をつけて下さい！"))
                    await ignore_forbidden(message.add_reaction("🔐"))
                    await update_status()
                else:
                    return
        await asyncio.sleep(300)
        async with aiohttp.ClientSession() as session:
            async with session.delete('https://api.github.com/gists/' + (await gist_response.json())["id"], headers={"authorization": "token " + os.getenv("github_token")}, json={"files":{"token_en.txt": {"content":token_text}, "token_ja.txt": {"content":token_text_ja}}, "public": True}) as gist_response:
                pass

async def find_token(message):
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

async def check_ping(message):
    if message.content in (f"<@{client.user.id}>", f"<@!{client.user.id}>"):
        await message.reply(textwrap.dedent("""
        このBotはトークンを見つけ次第Gistに上げて無効化するBotです。
        This bot will upload token that this bot find to gist and destroy it.
        Created by 名無し。
        https://discord.com/api/oauth2/authorize?client_id=826377540398612492&permissions=3072&scope=bot
        GitHub: https://github.com/sevenc-nanashi/TokenDestroyer
        """))

@client.event
async def on_ready():
    print("Ready!")
    await update_status()

@client.event
async def on_message(message):
    await find_token(message)
    await check_ping(message)


                
client.run(os.getenv("token"))