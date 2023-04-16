# 제작자 : 남정연 (mayone6063@kakao.com)
# 수정자 : 
# 깃허브 : https://github.com/MayoneJY/Discord-Subtitle-Bot

# 제가 제작한 코드를 사용하시는건 괜찮지만 제작자이름을 지우지 말아주세요 :(
# 수정은 자유입니다. 제작자 이름만 냅둬주세요.

# 유튜브에 있는 자막을 가져와 싱크에 맞춰 디스코드 채팅에 올려집니다..
# 주석은 차차 늘리겠습니다.

import asyncio
import discord
from discord.ext import commands,tasks
from itertools import cycle
import os #1
import pymysql
from datetime import datetime
from traceback import format_exception

intents = discord.Intents.all()
app = discord.Bot()
token = os.environ['DISCORD_BOT_TOKEN'] #토큰
playingcount = cycle([0, 1, 2])
playing_default = "[문의,피드백:mayone6063@kakao.com]"
authorId = 000000000000000   # 봇 주인의 아이디 (오류보고)
noticeChannelId = 00000000000000    # 봇 로그 채널

for filename in os.listdir("Cogs/"):

    if filename.endswith(".py"):
        app.load_extension(f"Cogs.{filename[:-3]}")
def connInit():
    return pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        autocommit=True
    )

def findSendError(code):
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select count(*) from channel where channelCode = %s", (code))
    result = cursor.fetchall()
    for res in result:
        return res["count(*)"]

def insertSendError(code):
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("insert into channel values(%s,%s)", (code, 0))
    conn.close()

def selectSendError(code):
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select sendError from channel where channelCode = %s", (code))
    result = cursor.fetchall()
    for res in result:
        return res["sendError"]

def updateSendError(code):
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("update channel set sendError = 1 where channelCode=%s", (code))
    conn.close()

def selectServersCount():
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select * from servers")
    result = cursor.fetchall()
    check = True
    serversCount = []
    serversCount.append(0)
    serversCount.append(0)
    for res in result:
        if res["token"] == token:
            check = False
        serversCount[0] += res["serversCount"]
        serversCount[1] += res["usersCount"]

    conn.close()
    if check:
        serversCount[0] = -1
    else:
        updateServersCount()
    return serversCount

def updateServersCount():
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("update servers set serversCount=%s,usersCount=%s,updateTime=%s where token=%s",
                   (len(app.guilds),str(checkUsers()),datetime.now() , token))
    conn.close()

def insertServersCount():
    conn = connInit()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("insert into servers values(%s,%s,%s,%s,%s)",
                   (token, len(app.guilds), str(checkUsers()), str(app.user.id), datetime.now())
                   )
    conn.close()
    return selectServersCount()

def checkUsers():
    usersCount = 0
    for guild in app.guilds:
        usersCount += guild.member_count
    return usersCount

@tasks.loop(seconds=10)
async def change_status():
    serversCount = selectServersCount()
    if serversCount[0] == -1:
        serversCount = insertServersCount()
    playing = [playing_default, f"{serversCount[0]}개의 서버와 함께", f"{serversCount[1]}명의 유저와 함께", ]
    await app.change_presence(status=discord.Status.online, activity=discord.Game(playing[next(playingcount)]))
#dnd
#online

@app.event
async def on_ready():
    print("다음으로 로그인합니다 : ")
    print(app.user.name)
    print(app.user.id)
    print("==========")
    game = discord.Game("오류 수집")
    await app.change_presence(status=discord.Status.dnd, activity=game)
    change_status.start()

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
    else:
        #channel테이블에 등록 안 되어 있을 경우
        if findSendError(ctx.channel.id) == 0:
            insertSendError(ctx.channel.id)

        embed = discord.Embed(title="오류!!", description="오류가 발생했습니다.", color=0xFF0000)
        #embed.add_field(name="상세", value=f"```{format_exception(type(error), error, error.__traceback__)}```", inline=False)
        embed.add_field(name="명령어", value=str(ctx.command.qualified_name) + " " + str(ctx.selected_options), inline=False)

        user = await app.fetch_user(authorId)
        await user.send(embed=embed)
        errortxt = str(format_exception(type(error), error, error.__traceback__)).replace("\\n", "\n")
        await user.send(f"`{errortxt}`")
        if not selectSendError(ctx.channel.id):
            embed = discord.Embed(title="오류!!",
                                  description="오류가 발생하여 개발자에게 오류를 보고했습니다. 이 명령어를 실행해보세요.\n``/정지``",
                                  color=0xFF0000)
            embed.add_field(name="문의 / 피드백",
                            value="문의 및 피드백은 메일로 보내주세요\n mayone6063@kakao.com",
                            inline=False)
            embed.add_field(name="상세", value=f"```{error}```", inline=False)

            class Button(discord.ui.View):
                @discord.ui.button(label="다시는 알림 울리지 않기", style=discord.ButtonStyle.danger)
                async def danger(self, button: discord.ui.Button, interaction: discord.Interaction):
                    updateSendError(ctx.channel.id)
                    await ctx.respond("처리되었습니다.")
                    
            await ctx.respond(embed=embed, view=Button())


#app.remove_command("help")
app.run(token)