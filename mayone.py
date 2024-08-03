import asyncio
import discord
from discord.ext import commands,tasks
from discord.errors import DiscordException
from itertools import cycle
import os #1
from datetime import datetime
from traceback import format_exception
from dotenv import load_dotenv
import os

load_dotenv()
# test
intents = discord.Intents.all()
app = discord.Bot()
token = os.getenv('DISCORD_BOT_TOKEN')
playingcount = cycle([0, 1, 2])
playing_default = "[문의,피드백:mayone6063@kakao.com]"
authorId = int(os.getenv('DISCORD_BOT_AUTHOR_ID'))   # 봇 주인의 아이디 (오류보고)
noticeChannelId = int(os.getenv('DISCORD_BOT_NOTICE_CHANNEL_ID'))    # 봇 로그 채널

for filename in os.listdir("Cogs/"):
    # for filename in os.listdir("D:\\디스코드봇\\newbot\\Cogs"): #2

    if filename.endswith(".py"):
        app.load_extension(f"Cogs.{filename[:-3]}")


@app.event
async def on_ready():
    print("다음으로 로그인합니다 : ")
    print(app.user.name)
    print(app.user.id)
    print("==========")
    game = discord.Game("오류 수집")
    await app.change_presence(status=discord.Status.dnd, activity=game)

@app.command(name="리로드")
async def reload_commands(ctx, extension=None):
    if int(ctx.author.id) == authorId:
        if extension is None: # extension이 None이면 (그냥 !리로드 라고 썼을 때)
            for filename in os.listdir("Cogs/"):
                if filename.endswith(".py"):
                    app.unload_extension(f"Cogs.{filename[:-3]}")
                    app.load_extension(f"Cogs.{filename[:-3]}")
                    await ctx.send(":white_check_mark: 모든 명령어를 다시 불러왔습니다!")
        else:
            app.unload_extension(f"Cogs.{extension}")
            app.load_extension(f"Cogs.{extension}")
            await ctx.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다!")


@app.command(name="상태")
async def edit_status(ctx, *, result):
    global playing_default
    if int(ctx.author.id) == authorId:
        playing_default = result

@app.event
async def on_guild_join(guild):
    channel = app.get_channel(noticeChannelId)
    await channel.send(f"봇이 어느 서버에 추가되었습니다. ``{len(app.guilds)}``")
    return

@app.event
async def on_guild_remove(guild):
    channel = app.get_channel(noticeChannelId)
    await channel.send(f"봇이 어느 서버에 제거되었습니다. ``{len(app.guilds)}``")
    return

@app.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(title="오류!!", description="봇에 권한이 없습니다!.", color=0xFF0000)
        embed.add_field(name="상세", value=f"```{error}```", inline=False)

        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="오류!!", description="명령어 사용이 잘못됐습니다.", color=0xFF0000)
        embed.add_field(name="상세", value=f"```{error}```", inline=False)

        await ctx.send(embed=embed)
    elif isinstance(error, DiscordException):
        if "CustomError: " in str(error) :
            embed = discord.Embed(color=0xFE676E)
            embed.add_field(name="오류 발생", value=f"{str(error).split('CustomError: ')[1]}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="오류!!", description="오류가 발생했습니다.", color=0xFF0000)
            embed.add_field(name="상세", value=f"```{format_exception(type(error), error, error.__traceback__)}```", inline=False)
            embed.add_field(name="명령어", value=str(ctx.command.qualified_name) + " " + str(ctx.selected_options), inline=False)

            user = await app.fetch_user(authorId)
            errortxt = str(format_exception(type(error), error, error.__traceback__)).replace("\\n", "\n")
            errortxt_chunks = [errortxt[i:i+1000] for i in range(0, len(errortxt), 1000)]
            for chunk in errortxt_chunks:
                await user.send(f"```{chunk}```")
            print(errortxt)
    else:

        embed = discord.Embed(title="오류!!", description="오류가 발생했습니다.", color=0xFF0000)
        embed.add_field(name="상세", value=f"```{format_exception(type(error), error, error.__traceback__)}```", inline=False)
        embed.add_field(name="명령어", value=str(ctx.command.qualified_name) + " " + str(ctx.selected_options), inline=False)

        user = await app.fetch_user(authorId)
        errortxt = str(format_exception(type(error), error, error.__traceback__)).replace("\\n", "\n")
        errortxt_chunks = [errortxt[i:i+1000] for i in range(0, len(errortxt), 1000)]
        for chunk in errortxt_chunks:
            await user.send(f"```{chunk}```")
        print(errortxt)


#app.remove_command("help")

try: 
    app.run(token)
except Exception as e:
    print(f'Error: {e}')