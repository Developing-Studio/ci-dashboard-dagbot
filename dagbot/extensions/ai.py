"""
    Dagbot is a discord meme bot that does nothing useful
    Copyright (C) 2020  Daggy1234

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import json

import async_cleverbot as ac
import discord
from discord.ext import commands
from utils.converters import ImageConverter


class ai(commands.Cog):
    """Interact with the ai's of today (long way to go)"""

    def __init__(self, client):
        self.client = client
        self.cleverbot = ac.Cleverbot(self.client.data["cbkey"])
        self.gapikey = self.client.data["gapikey"]
        self.cleverbot.set_context(ac.DictContext(self.cleverbot))

    async def cog_check(self, ctx):
        g_id = str(ctx.guild.id)
        for e in self.client.cogdata:
            if str(e["serverid"]) == str(g_id):
                if e["ai"]:
                    return True
                else:
                    return False

    async def ocra(self, ur):
        url = f"https://eu-vision.googleapis.com/v1/images:annotate?key={self.gapikey}"
        payload = {
            "requests": [
                {
                    "image": {"source": {"imageUri": ur}},
                    "features": [{"type": "TEXT_DETECTION"}],
                }
            ]
        }
        payload = str(payload)

        headers = {
            "content-type": "application/json",
            "Accept-Charset": "UTF-8"}
        r = await self.client.session.post(url, data=payload, headers=headers)
        js = await r.json()

        try:
            f = js["responses"][0]
            df = f["textAnnotations"]
        except BaseException:
            return False

        mst = ""
        e = df[0]
        mst = mst + str(e["description"])
        return mst

    async def labela(self, ur):
        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.gapikey}"
        payload = {
            "requests": [
                {
                    "image": {"source": {"imageUri": ur}},
                    "features": [{"type": "LABEL_DETECTION", "maxResults": 5}],
                }
            ]
        }

        payload = str(payload)

        headers = {
            "content-type": "application/json",
            "Accept-Charset": "UTF-8"}
        r = await self.client.session.post(url, data=payload, headers=headers)
        js = await r.json()
        try:
            f = js["responses"][0]["labelAnnotations"]
        except BaseException:
            return False
        mst = ""
        for e in f:
            mst = mst + f"\n{e['description']}\t{e['score']}"
        return mst

    async def captioni(self, ur):
        data = {
            "Content": ur,
            "Type": "CaptionRequest",
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        url = "https://captionbot.azurewebsites.net/api/messages"

        r = await self.client.session.post(url, data=json.dumps(data), headers=headers)
        t = await r.text()
        return t
        # if not r.ok:
        #     return(None)
        # res = r.text[1:

    async def imgen(self, text):
        r = await self.client.session.post(
            "https://api.deepai.org/api/text2img",
            data={"text": text, },
            headers={"api-key": self.client.data["deepapikey"]},
        )
        js = await r.json()
        return js["output_url"]

    @commands.command(cooldown_after_parsing=True, aliases=["chatbot", "ask", "converse"])
    async def chat(self, ctx, *, query: str):
        await ctx.trigger_typing()
        try:
            r = await self.cleverbot.ask(query, ctx.author.id)
        except BaseException:
            await ctx.send('An error occurred! We will try and fix')

        else:
            return await ctx.send(f"> {query}\n{ctx.author.mention} {r.text}")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def caption(self, ctx, *, source=None):
        image_url = await ImageConverter.convert(ctx, source)
        f = await self.captioni(image_url)
        if not f:
            return await ctx.send("No results as of now. Shit be wonky")
        else:
            embed = discord.Embed(title=f, color=ctx.guild.me.color)
            embed.set_image(url=image_url)
            return await ctx.send(embed=embed)

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate(self, ctx, *, text):
        resp = await self.imgen(text)
        embed = discord.Embed(
            title=f"Generated an image on your text {text}", color=ctx.guild.me.color
        )
        embed.set_image(url=resp)
        return await ctx.send(embed=embed)

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def ocr(self, ctx, *, source=None):
        image_url = await ImageConverter.convert(ctx, source)
        f = await self.ocra(image_url)
        if not f:
            return await ctx.send("No results rn")
        else:
            embed = discord.Embed(
                title=f"Your Image contains the following text",
                description=f,
                color=ctx.guild.me.color,
            )
            embed.set_image(url=image_url)
            return await ctx.send(embed=embed)

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def label(self, ctx, *, source=None):
        image_url = await ImageConverter.convert(ctx, source)
        y = await self.labela(image_url)
        if not y:
            return await ctx.send("No results as of now. Shit be wonky")
        else:
            embed = discord.Embed(
                title="We have generated labels for your image!",
                description=y,
                color=ctx.guild.me.color,
            )
            return await ctx.send(embed=embed)


def setup(client):
    client.add_cog(ai(client))
