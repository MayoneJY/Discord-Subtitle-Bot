import asyncio
import math

from yt_dlp import YoutubeDL
import ffmpeg
import discord
import time as t
from bs4 import BeautifulSoup
import urllib
from urllib import parse
import json
import discord
from discord.ui import Select, View, Button
from discord.ext import commands
from discord.commands import slash_command, Option
import html
import pymysql
from datetime import datetime

noticeChannelId = 00000000000000    # 봇 로그 채널

tempCtx = None
test_c = 0
SubtitleLanguages = ["ko", "en", "ja"]
SubtitleTimes = {}
SubtitleCounts = {}
SubtitleTexts = {}
SubtitleNowTimes = {}
SubtitleLanguageChangeCheck = {}
SubtitleTitle = {}
Ctx = {}

PauseSleep_t = {}
PauseSleep = {}
DefaultVolume = 0.1
NowVolumes = {}
PlayLists = {}
PlayList_count = {}
PlayList_max_count = {}
PlayLists_title = {}
ThumbnailList = {}
WhilePauses = {}
while_play = {}
CheckStops = {}
subtitletextlanguage = {}
Playauthor = {}
PlayPauses = {}
Playing = {}
PlayList_ERROR = {}
playNow = {}
Messages = {}
PlayRepeat = {}
voice = {}


SearchingData = {}

# 해야할것
# 재생목록 예약할 때 50번 째 넘는 것도 예약하기
# 예약 몇개 되었는지 누가 추가했는지 만들기

#데이터베이스

table_sql = "select count(*) from music_info where url_id=%s"
table_sql_title_insert = "insert into music_info values(%s,%s,%s,%s)"
table_sql_select = "select * from music_info where url_id=%s"
subtitle_sql_create_ko_1 = "create table "
subtitle_sql_create_ko_2 = """_subtitle_ko(
time int(5),
subtitle varchar(100))
"""
subtitle_sql_create_en_1 = "create table "
subtitle_sql_create_en_2 = """_subtitle_en(
time int(5),
subtitle varchar(100))
"""
subtitle_sql_create_jp_1 = "create table "
subtitle_sql_create_jp_2 = """_subtitle_jp(
time int(5),
subtitle varchar(100))
"""
search_sql = "select count(url_id) from search where title = %s"
search_sql_insert = "insert into search values(%s,%s)"
search_sql_select = "select url_id from search where title = %s"

ytdl_format_options = {
    'writesubtitles': True,
    'subtitleslangs': SubtitleLanguages,
    'writethumbnail' : True,
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

#ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
ydl = YoutubeDL(ytdl_format_options)

def connInit():
    return pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        autocommit=True
    )

def setup(app):
    app.add_cog(Core(app))

##### PlayingButtons

class PlayingButtonPrev(Button):
    def __init__(self, ctx, disabled):
        super().__init__(label="이전 곡", emoji="⏮", disabled=disabled)
        self.ctx = ctx

    async def callback(self, interaction):
        await Core.prev(self.ctx)

class PlayingButtonPause(Button):
    def __init__(self, ctx):
        super().__init__(label="일시 정지", emoji="⏸")
        self.ctx = ctx

    async def callback(self, interaction):
        if self.label == "일시 정지":
            await Core.pause(self.ctx)
            self.label = "다시 재생"
            self.style=discord.ButtonStyle.danger
            self.emoji="▶️"
        else:
            await Core.resume(self.ctx)
            self.label = "일시 정지"
            self.style=discord.ButtonStyle.gray
            self.emoji="⏸"
        try:
            view = View(timeout=None)
            view.add_item(PlayingButtonPrev(self.ctx, True if PlayList_count[self.ctx.channel.id] == 0 else False))
            view.add_item(self)
            view.add_item(PlayingButtonNext(self.ctx))
            view.add_item(PlayingButtonStop(self.ctx))
            repeat = PlayRepeat[self.ctx.channel.id]
            repeat_label = "반복 재생 안함" if repeat == 0 else "반복 재생" if repeat == 1 else "한 곡 반복 재생"
            repeat_style = discord.ButtonStyle.gray if repeat == 0 else discord.ButtonStyle.primary
            view.add_item(PlayingButtonRepeat(self.ctx, repeat_label, repeat_style))
            await interaction.response.edit_message(view=view)
        except:
            pass

class PlayingButtonNext(Button):
    def __init__(self, ctx):
        super().__init__(label="다음 곡", emoji="⏭")
        self.ctx = ctx

    async def callback(self, interaction):
        await Core.skip(self.ctx)

class PlayingButtonStop(Button):
    def __init__(self, ctx):
        super().__init__(label="정지", emoji="⏹", style=discord.ButtonStyle.danger)
        self.ctx = ctx

    async def callback(self, interaction):
        await Core.stop(self.ctx)

class PlayingButtonRepeat(Button):
    def __init__(self, ctx, label, style):
        #print(1)
        super().__init__(label=label, emoji="➡️", style=style)
        self.ctx = ctx

    async def callback(self, interaction):
        if PlayRepeat[self.ctx.channel.id] == 0:
            self.label = "반복 재생"
            self.emoji = "🔁"
            self.style = discord.ButtonStyle.primary
            PlayRepeat[self.ctx.channel.id] = 1
        elif PlayRepeat[self.ctx.channel.id] == 1:
            self.label = "한곡 반복 재생"
            self.emoji = "🔂"
            PlayRepeat[self.ctx.channel.id] = 2
        else:
            self.label = "반복 재생 안함"
            self.emoji = "➡️"
            self.style = discord.ButtonStyle.gray
            PlayRepeat[self.ctx.channel.id] = 0

        try:
            view = View(timeout=None)
            view.add_item(PlayingButtonPrev(self.ctx, True if PlayList_count[self.ctx.channel.id] == 0 else False))
            view.add_item(PlayingButtonPause(self.ctx))
            view.add_item(PlayingButtonNext(self.ctx))
            view.add_item(PlayingButtonStop(self.ctx))
            view.add_item(self)
            await interaction.response.edit_message(view=view)
        except:
            pass

##### /PlayingButtons


class SearchButtons(discord.ui.View):
    def __init__(self, self2, ctx, data):
        super().__init__()
        self.self = self2
        self.ctx = ctx
        self.data = data
        self.count = 0
        self.maxCount = len(data)/2

    @discord.ui.button(label="이전", style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="prev", disabled=True)
    async def prev_button_callback(self, button, interaction):
        self.count -= 1
        if self.count == 0:
            button.disabled = True
        if self.maxCount > 1:
            button1 = [x for x in self.children if x.custom_id=="next"][0]
            button1.disabled = False
        embed_que = discord.Embed(title=self.data[self.count * 2 + 1], url="https://www.youtube.com/watch?v=" +
                                                                              self.data[self.count*2])
        embed_que.set_image(url="https://i.ytimg.com/vi/" + self.data[self.count*2] + "/hqdefault.jpg")
        try:
            await interaction.response.edit_message(embed=embed_que, view=self)
        except:
            pass

    @discord.ui.button(label="다음", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next")
    async def next_button_callback(self, button, interaction):
        self.count += 1
        if self.count == self.maxCount - 1:
            button.disabled = True
        if self.count > 0:
            button1 = [x for x in self.children if x.custom_id=="prev"][0]
            button1.disabled = False
        embed_que = discord.Embed(title=self.data[self.count * 2 + 1], url="https://www.youtube.com/watch?v=" +
                                                                              self.data[self.count*2])
        embed_que.set_image(url="https://i.ytimg.com/vi/" + self.data[self.count*2] + "/hqdefault.jpg")

        try:
            await interaction.response.edit_message(embed=embed_que, view=self)
        except:
            pass

    @discord.ui.button(label="추가", style=discord.ButtonStyle.green, emoji="⤴️")
    async def add_button_callback(self, button, interaction):
        try:
            await interaction.response.edit_message(delete_after=0)
        except:
            pass

        await Core.play_first(self.self, self.ctx, url="https://www.youtube.com/watch?v=" + self.data[self.count*2])

    @discord.ui.button(label="취소", style=discord.ButtonStyle.danger, emoji="⤵️")
    async def cancel_button_callback(self, button, interaction):
        try:
            await interaction.response.edit_message(delete_after=0)
        except:
            pass

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        # self.progress = data.get('progress')

    @classmethod
    async def from_url(cls, ctx, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))


        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        # print(data)
        filename = data['url'] if stream else ydl.prepare_filename(data)
        filenametemp = list(filename)
        for i in range(0, 5):
            filenametemp.pop()

        for i in range(3):
            #print(i)
            SubtitleTitle[ctx.channel.id][i] = ''.join(filenametemp) + "." + SubtitleLanguages[i] + ".vtt"
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def from_title(cls, ctx, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch5:{url}", download=stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        data2 = []
        data2.append(data[0]['id'])
        data2.append(data[0]['title'])
        try:
            if len(data[0]) >= 5:
                for i in range(1, 5):
                    data2.append(data[i]['id'])
                    data2.append(data[i]['title'])
            else:
                for i in range(1, len(data[0])):
                    data2.append(data[i]['id'])
                    data2.append(data[i]['title'])
        except:
            pass

        SearchingData[ctx.channel.id] = data2


class Core(commands.Cog, name="뮤직봇"):

    def __init__(self, app):
        global buttons
        self.app = app

    @slash_command(name="예약목록", description="예약목록을 확인합니다.")
    async def que_view(self, ctx):
        global PlayList_count
        send_que_txt = "```py\n"
        send_que_txt2 = "```cs\n"
        send_que_chk = False
        i = 1
        for que_txt in range(len(PlayLists[ctx.channel.id])):
            if i == 1:
                i += 1
                continue
            if PlayList_count[ctx.channel.id] + 2 == i:
                if len(send_que_txt + "@[~재생중~] ") >= 2000:
                    send_que_chk = True
                    send_que_txt2 += "@[~재생중~] "
                else:
                    send_que_txt += "@[~재생중~] "
            if len(send_que_txt + str(i - 1) + ". " + PlayLists_title[ctx.channel.id][i - 2] + "\n") >= 2000:
                send_que_chk = True
                send_que_txt2 += str(i - 1) + ". " + PlayLists_title[ctx.channel.id][i - 2] + "\n"
            else:
                send_que_txt += str(i - 1) + ". " + PlayLists_title[ctx.channel.id][i - 2] + "\n"
            i += 1

        send_que_txt = send_que_txt + "```"
        send_que_txt2 = send_que_txt2 + "```"
        await ctx.respond(content=send_que_txt, delete_after=20)
        if send_que_chk:
            await ctx.respond(content=send_que_txt2, delete_after=20)

    @slash_command(name="볼륨", description="볼륨을 조정합니다.")
    async def volume(self, ctx, volume: Option(int, "0 ~ 100 사이를 입력하세요.", min_value=0, max_value=100)):
        if ctx.voice_client is None:
            return await ctx.respond("음성 채널에 연결이 되어있지 않습니다.", delete_after=5)

        NowVolumes[ctx.channel.id] = volume / 100
        ctx.voice_client.source.volume = NowVolumes[ctx.channel.id]
        await ctx.respond("볼륨을 {}%로 변경했습니다.".format(volume))

    @slash_command(name="일시정지", description="음악을 일시정지합니다.")
    async def pause(self, ctx):
        global PauseSleep, PauseSleep_t
        PauseSleep_t[ctx.channel.id] = t.time()
        ctx.voice_client.pause()
        PlayPauses[ctx.channel.id] = True
        await ctx.respond("음악을 일시정지합니다.", delete_after=5)

    @slash_command(name="다시재생", description="일시 정지한 음악을 재생합니다.")
    async def resume(self, ctx):
        global PauseSleep, PauseSleep_t
        PauseSleep[ctx.channel.id] += t.time() - PauseSleep_t[ctx.channel.id]
        PlayPauses[ctx.channel.id] = False
        if ctx.voice_client:
            ctx.voice_client.resume()
            await ctx.respond("음악을 다시 재생합니다.", delete_after=5)

    @slash_command(name="입장", description="음성채널에 입장합니다.")
    async def join(self, ctx):

        if ctx.author.voice and ctx.author.voice.channel:  # 채널에 들어가 있는지 파악
            channel = ctx.author.voice.channel  # 채널 구하기
            await channel.connect()  # 채널 연결
            await ctx.respond("봇이 음성채널에 입장했습니다.", delete_after=5)
        else:  # 유저가 채널에 없으면
            await ctx.respond("음성채널에 연결되지 않았습니다.", delete_after=5)  # 출력

    @slash_command(name="정지", description="음악을 정지한 뒤 봇을 추방합니다.")
    async def stop(self, ctx):
        self.check_variable(ctx)
        global WhilePauses, CheckStops
        Playing[ctx.channel.id] = False
        CheckStops[ctx.channel.id] = True
        WhilePauses[ctx.channel.id] = False
        try:
            await ctx.voice_client.disconnect()
            await ctx.respond("음악을 정지하고 채널에서 떠납니다..", delete_after=5)
        except:
            await ctx.respond("음악이 재생 중이 아니거나 봇이 채널에 없습니다!", delete_after=5)

    @slash_command(name="스킵", description="노래를 정지하고 다음 곡을 들려줍니다.")
    async def skip(self, ctx):
        self.check_variable(ctx)
        global CheckStops
        try:
            CheckStops[ctx.channel.id] = True
            ctx.voice_client.stop()
            await ctx.respond("음악을 스킵합니다.", delete_after=5)
        except:
            await ctx.respond("음악이 재생 중이 아니거나 봇이 채널에 없습니다!", delete_after=5)

    @slash_command(name="이전곡", description="노래를 정지하고 이전 곡을 들려줍니다.")
    async def prev(self, ctx):
        self.check_variable(ctx)
        global CheckStops
        try:
            if PlayList_count[ctx.channel.id] - 2 < -1:
                await ctx.respond("이전 곡이 없습니다!", delete_after=5)
                return
            CheckStops[ctx.channel.id] = True
            PlayList_count[ctx.channel.id] -= 2
            ctx.voice_client.stop()
            await ctx.respond("음악을 스킵합니다.", delete_after=5)
        except:
            await ctx.respond("음악이 재생 중이 아니거나 봇이 채널에 없습니다!", delete_after=5)


    async def new_import_subtitles(self, ctx):
        for lang in range(3):
            try:
                f = open(SubtitleTitle[ctx.channel.id][lang], 'r', encoding='UTF8')
                lines = f.readlines()
                i = 1
                tempTimes = []
                tempSubtiles = []
                chk = False
                timeChk = True
                for line in lines:
                    if line == "\n":
                        continue
                    if timeChk:
                        if line.find("-->") == -1 or line.find(":") == -1:
                            i += 1
                            continue
                        else:
                            timeChk = False


                    if line.find("-->") >= 0 and line.find(":") >= 0:
                        #time
                        h = line[0:2]
                        m = line[3:5]
                        s = line[6:8]
                        t = line[9:10]
                        time = float(str(int(h) * 360 + int(m) * 60 + int(s)) + "." + t)
                        tempTimes.append(time)
                        chk = True

                    else:
                        #subtitle
                        temp = list(line)
                        temp.pop()
                        if chk:
                            tempSubtiles.append(BeautifulSoup(''.join(temp), "lxml").text.replace("\u200b", ""))

                        else:
                            tempSubtiles[-1] += "\n" + BeautifulSoup(''.join(temp), "lxml").text.replace("\u200b", "")

                        chk = False

                    i += 1

                appendcount = 0
                subtitleCount = 0
                for time in tempTimes:
                    if appendcount != 0:
                        if round(time) - round(SubtitleTimes[ctx.channel.id][lang][appendcount - 1]) < 1:
                            if SubtitleTexts[ctx.channel.id][lang][appendcount - 1].find(tempSubtiles[subtitleCount]) == -1:
                                SubtitleTexts[ctx.channel.id][lang][appendcount - 1] += "\n" + tempSubtiles[subtitleCount]
                        else:
                            if str(SubtitleTexts[ctx.channel.id][lang][appendcount - 1]).find(tempSubtiles[subtitleCount]) == -1:
                                SubtitleTimes[ctx.channel.id][lang].append(round(time))
                                SubtitleTexts[ctx.channel.id][lang].append(tempSubtiles[subtitleCount])
                                appendcount += 1
                    else:
                        SubtitleTimes[ctx.channel.id][lang].append(round(time))
                        SubtitleTexts[ctx.channel.id][lang].append(tempSubtiles[subtitleCount])
                        appendcount += 1
                    subtitleCount += 1
                appendcount = 0
                for temp in SubtitleTexts[ctx.channel.id][lang]:
                    if len(temp) > 200:
                        SubtitleTexts[ctx.channel.id][lang].clear()
                        SubtitleTexts[ctx.channel.id][lang].append("자막이 비정상적이므로 불러오지 않았습니다.")
                        SubtitleTimes[ctx.channel.id][lang].clear()
                        SubtitleTimes[ctx.channel.id][lang].append(9999)
                    appendcount += 1

                SubtitleTexts[ctx.channel.id][lang].append("끝")
                for j in range(1, 5):
                    SubtitleTexts[ctx.channel.id][lang].append("--------")
                    SubtitleTimes[ctx.channel.id][lang].append(9999)

                try:
                    if SubtitleTimes[ctx.channel.id][lang][
                        SubtitleCounts[ctx.channel.id]] == 9999:
                        sub_chk = True
                        pass
                except IndexError:
                    pass

            except FileNotFoundError:
                SubtitleTexts[ctx.channel.id][lang].append("YouTube에 자막(CC)이 없습니다!")
                for j in range(1, 5):
                    SubtitleTexts[ctx.channel.id][lang].append("--------")
                    SubtitleTimes[ctx.channel.id][lang].append(9999)


    
    def playlist_choices():
        #Ctx[ctx.channel.id] = ctx


        conn = connInit()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select * from quantity order by quantity desc")
        result = cursor.fetchall()
        options = []
        chk2 = 1
        for res in result:
            channel = ""
            if len(res["channel"]) > 17:
                chk = 1
                for strr in res["channel"]:
                    channel += strr
                    chk += 1
                    if chk > 15:
                        channel += ".."
                        break
            else:
                channel = res["channel"]
            options.append(channel)
            chk2 += 1
            if chk2 > 24:
                break

        conn.close()
        return options

    @slash_command(name="테스트", description="테스트입니다.")
    async def testt(self, ctx):
        await YTDLSource.from_url(ctx, "타바코", loop=self.app.loop)

    @slash_command(name="재생목록", description="서버에 저장된 재생목록을 재생합니다.")
    async def playlist(self, ctx, playlist:Option(str, "재생목록을 선택하세요.", choices=playlist_choices())):

        if ctx.voice_client is None and not ctx.author.voice:
            return
        conn = connInit()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select * from quantity order by quantity desc")
        result = cursor.fetchall()
        for res in result:
            if playlist == str(res["channel"]):
                cursor.execute("select url_id from music_info where channel=%s", playlist)
                result_info = cursor.fetchall()

                # 배열이 있는지 확인
                self.check_variable(ctx)

                # 배열 초기화
                try:
                    ctx.voice_client.stop()
                except:
                    pass
                voice[ctx.guild.id] = ctx.channel
                Ctx[ctx.channel.id] = ctx
                WhilePauses[ctx.channel.id] = False
                CheckStops[ctx.channel.id] = True
                while_play[ctx.channel.id] = False
                PlayPauses[ctx.channel.id] = False
                PauseSleep[ctx.channel.id] = 0
                PauseSleep_t[ctx.channel.id] = 0
                await asyncio.sleep(0.1)
                SubtitleLanguageChangeCheck[ctx.channel.id] = True
                SubtitleCounts[ctx.channel.id] = 0
                PlayList_count[ctx.channel.id] = 0
                try:
                    for i in range(0, 3):
                        SubtitleTexts[ctx.channel.id][i].clear()
                        SubtitleTimes[ctx.channel.id][i].clear()
                        SubtitleTitle[ctx.channel.id][i].clear()
                except AttributeError:
                    SubtitleTexts[ctx.channel.id] = []
                    SubtitleTimes[ctx.channel.id] = []
                    SubtitleTitle[ctx.channel.id] = []
                    
                    for i in range(0, 3):
                        SubtitleTexts[ctx.channel.id].append([i])
                        SubtitleTimes[ctx.channel.id].append([i])
                        SubtitleTitle[ctx.channel.id].append([i])
                    
                    for i in range(0, 3):
                        SubtitleTexts[ctx.channel.id][i].clear()
                        SubtitleTimes[ctx.channel.id][i].clear()
                        SubtitleTitle[ctx.channel.id][i].clear()

                SubtitleNowTimes[ctx.channel.id] = 0
                PlayLists[ctx.channel.id].clear()
                ThumbnailList[ctx.channel.id].clear()
                Playauthor[ctx.channel.id].clear()

                for res2 in result_info:
                    await self.select_table(ctx, str(res2["url_id"]), cursor)
                await ctx.respond("``재생목록을 추가합니다.``", delete_after=3)
                await self.player(ctx)

        conn.close()


    # @slash_command(name="내재생목록", description="나만의 재생목록을 재생합니다.")
    # async def myplaylist(self, ctx):

    #     if ctx.voice_client is None and not ctx.author.voice:
    #         return
    #     try:
    #         type(Messages[ctx.channel.id])
    #     except KeyError:
    #         Messages[ctx.channel.id] = []

    #     conn = connInit()
    #     cursor = conn.cursor(pymysql.cursors.DictCursor)
    #     cursor.execute("select DISTINCT playlistTitle from playlists where uid = %s", ctx.author.id)
    #     result = cursor.fetchall()
    #     options = []
    #     chk2 = 1
    #     for res in result:
    #         channel = ""
    #         if len(res["playlistTitle"]) > 17:
    #             chk = 1
    #             for strr in res["playlistTitle"]:
    #                 channel += strr
    #                 chk += 1
    #                 if chk > 14:
    #                     channel += ".."
    #                     break
    #         else:
    #             channel = res["playlistTitle"]
    #         options.append(discord.SelectOption(label=res["playlistTitle"], emoji="🎵"))
    #         chk2 += 1
    #         if chk2 > 24:
    #             break
    #     conn.close()
    #     select = Select(options=options)
    #     #print(ctx.channel.id)
    #     async def my_callback(interaction):
    #         await Messages[interaction.channel_id].delete()
    #         conn = connInit()
    #         cursor = conn.cursor(pymysql.cursors.DictCursor)
    #         cursor.execute("select * from playlists where uid = %s and playlistTitle = %s",
    #                        (str(interaction.user.id),
    #                         str(select.values[0])))

    #         # 배열이 있는지 확인
    #         self.check_variable(Ctx[interaction.channel_id])

    #         # 배열 초기화
    #         try:
    #             Ctx[interaction.channel_id].voice_client.stop()
    #         except:
    #             pass
    #         WhilePauses[interaction.channel_id] = False
    #         CheckStops[interaction.channel_id] = True
    #         while_play[interaction.channel_id] = False
    #         PlayPauses[interaction.channel_id] = False
    #         SubtitleTitle[interaction.channel_id] = []
    #         PauseSleep[interaction.channel_id] = 0
    #         PauseSleep_t[interaction.channel_id] = 0
    #         await asyncio.sleep(0.1)
    #         SubtitleLanguageChangeCheck[interaction.channel_id] = True
    #         SubtitleCounts[interaction.channel_id] = 0
    #         PlayList_count[interaction.channel_id] = 0
    #         for i in range(0, 3):
    #             SubtitleTexts[interaction.channel_id][i].clear()
    #             SubtitleTimes[interaction.channel_id][i].clear()
    #             SubtitleTitle[interaction.channel_id][i].clear()
    #         SubtitleNowTimes[interaction.channel_id] = 0
    #         PlayLists[interaction.channel_id].clear()
    #         ThumbnailList[interaction.channel_id].clear()
    #         Playauthor[interaction.channel_id].clear()

    #         result_info = cursor.fetchall()
    #         chk = 0
    #         for res2 in result_info:
    #             await self.select_table(Ctx[interaction.channel_id], str(res2["videoUrl"]), cursor)
    #             chk += 1
    #             if chk > 24:
    #                 break
    #         await interaction.send("``재생목록을 추가합니다.``", delete_after=3)
    #         await interaction.origin_message.delete()
    #         await self.player(Ctx[interaction.channel_id])

    #         conn.close()
    #     select.callback = my_callback
    #     view = View()
    #     view.add_item(select)
    #     Messages[ctx.channel.id] = await ctx.send("내 재생목록을 선택해주세요.", view=view)



    async def select_table(self, ctx, url_id, cursor):

        if len(url_id) > 5:
            if str(url_id[:5]) == "https":
                url_id = url_id[len("https://www.youtube.com/watch?v="):]
        cursor.execute(table_sql_select, url_id)
        result = cursor.fetchall()
        ThumbnailList[ctx.channel.id].append(result[0]['thumbnail'])
        PlayLists_title[ctx.channel.id].append(result[0]['title'])
        PlayLists[ctx.channel.id].append(f"https://www.youtube.com/watch?v={url_id}")
        PlayList_max_count[ctx.channel.id] += 1
        Playauthor[ctx.channel.id].append(ctx.author.id)

    async def insert_table_bool(self, ctx, url_id, cursor):
        try:
            data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?q=" +
                                          url_id + "&videoCaption=any&type=video&part=snippet" +
                                          "&key=AIzaSyDEfBsMmcstsyfWkA_32IKWDoiOKmppWkQ&maxResults=1").read()
            datajson = json.loads(data)
            cursor.execute(table_sql_title_insert,
                           (datajson["items"][0]["snippet"]["channelTitle"],
                            datajson["items"][0]["snippet"]["title"],
                            "https://i.ytimg.com/vi/" + datajson["items"][0]["id"]["videoId"] + "/hqdefault.jpg",
                            url_id)
                           )

            await self.insert_quantity(cursor, datajson["items"][0]["snippet"]["channelTitle"])
            await self.select_table(ctx, url_id, cursor)
        except:
            ThumbnailList[ctx.channel.id].append("https://i.ytimg.com/vi/" + url_id + "/hqdefault.jpg")
            PlayLists_title[ctx.channel.id].append("YouTube 검색 Api의 할당량이 초과되어 제목을 불러오지 못했습니다.")
            PlayLists[ctx.channel.id].append("https://www.youtube.com/watch?v=" + url_id)
            PlayList_max_count[ctx.channel.id] += 1
            Playauthor[ctx.channel.id].append(ctx.author.id)

    async def insert_table(self, ctx, url_id, cursor, datajson):
        cursor.execute(table_sql_title_insert,
                       (datajson["items"][0]["snippet"]["channelTitle"],
                        datajson["items"][0]["snippet"]["title"],
                        "https://i.ytimg.com/vi/" + datajson["items"][0]["id"]["videoId"] + "/hqdefault.jpg",
                        url_id)
                       )

        await self.insert_quantity(cursor, datajson["items"][0]["snippet"]["channelTitle"])
        await self.select_table(ctx, url_id, cursor)

    async def insert_quantity(self, cursor, channel_title):
        cursor.execute("select count(*) from quantity where channel = %s",
                       channel_title
                       )
        result = cursor.fetchone()
        if result['count(*)'] != 0:
            cursor.execute("select quantity from quantity where channel = %s",
                           channel_title
                           )
            result = cursor.fetchone()
            cursor.execute("update quantity set quantity=%s where channel=%s",
                           (int(result['quantity']) + 1,
                            channel_title))
        else:
            cursor.execute("insert into quantity values(%s,%s)",
                           (channel_title,
                            1))

    async def find_table(self, url_id, cursor):
        cursor.execute(table_sql, url_id)
        result = cursor.fetchone()
        return result['count(*)']

    async def search_urlid(self, url_id, cursor):
        cursor.execute(search_sql_select, url_id)
        result = cursor.fetchone()
        return result['url_id']


    async def player(self, ctx):
        async with ctx.typing():
            # 동영상이 재생이 되는지 확인

            WhilePauses[ctx.channel.id] = True
            while WhilePauses[ctx.channel.id]:
                loding_video = await ctx.send("``다운로드 및 영상을 불러오는 중..``")
                error_1 = False
                #print(PlayLists[ctx.channel.id])
                #print(PlayList_count[ctx.channel.id])
                url = PlayLists[ctx.channel.id][PlayList_count[ctx.channel.id]]
                try:
                    player = await YTDLSource.from_url(ctx, url, loop=self.app.loop)
                except:
                    try:
                        add_list_embed_message.delete()
                    except:
                        pass
                    await loding_video.delete()
                    await ctx.send("동영상 재생에 실패했습니다.", delete_after=20)
                    error_1 = True
                    PlayList_count[ctx.channel.id] += 1
                # play_button_view = PlayingButtons(ctx)
                # print(play_button_view)
                SubtitleCounts[ctx.channel.id] = 0
                SubtitleNowTimes[ctx.channel.id] = 0
                if not error_1:
                    channel = self.app.get_channel(noticeChannelId)
                    print_log = "``" + str(datetime.now()) + " Channel:" + str(ctx.guild.name) + " | Playing: " + str(player.title) + "``"
                    playNow[ctx.channel.id] = url
                    await channel.send(print_log)
                    print(print_log)
                    # 자막 불러오기
                    subtitletextlanguage[ctx.channel.id] = 0
                    test = 0
                    sub_chk = False
                    # for SLan in SubtitleLanguages:
                    #    await self.import_subtitles(ctx, url, SLan, test)
                    #    test += 1
                    await self.new_import_subtitles(ctx)

                    # 재생바
                    total_second = player.duration - (math.floor(player.duration / 60) * 60)
                    if total_second < 10:
                        total_second = "0" + str(total_second)
                    total_minute = math.floor(player.duration / 60)
                    total_second = str(total_second)
                    total_minute = str(total_minute)
                    # ctx.voice_client.play(player, after=lambda e: print("player error: %s" % e) if e else None)
                    # ctx.voice_client.source.volume = NowVolumes[ctx.channel.id]
                    embedtitle = discord.Embed(title=player.title, url=url)
                    embedtitle.set_author(name="현재 재생중~ 　 　 　 　 　 　 　 　 　 　 　 　 　 　")

                    # print(len(SubtitleTexts[ctx.channel.id][0]))
                    # print(len(SubtitleTexts[ctx.channel.id][1]))
                    # print(len(SubtitleTexts[ctx.channel.id][2]))
                    if len(SubtitleTexts[ctx.channel.id][0]) > 5:
                        subtitletextlanguage[ctx.channel.id] = 0
                    elif len(SubtitleTexts[ctx.channel.id][1]) > 5:
                        subtitletextlanguage[ctx.channel.id] = 1
                    elif len(SubtitleTexts[ctx.channel.id][2]) > 5:
                        subtitletextlanguage[ctx.channel.id] = 2

                    embedthumbnail = discord.Embed()
                    subtitle = ""
                    if ThumbnailList[ctx.channel.id][PlayList_count[ctx.channel.id]] != "Null":
                        embedthumbnail.set_image(url=ThumbnailList[ctx.channel.id][int(PlayList_count[ctx.channel.id])])
                        sendembedthumbnail = await ctx.send(embed=embedthumbnail)
                    try:
                        subtitle = "```yaml\n \n```" + "```brainfuck\n" + \
                                   SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                       SubtitleCounts[ctx.channel.id]] + "\n```"
                    except IndexError:
                        subtitle = "```yaml\n \n```" + "```brainfuck\n자막이 없습니다.\n```"
                    embedtitle.add_field(name="자막", value=subtitle, inline=False)
                    # progressbar = ""
                    # progressbar += "🔘"
                    # for j in range(1, 28):
                    #    progressbar += "▬"
                    # embedtitle.add_field(name="0:00 / " + str(total_minute) + ":" + str(total_second), value=progressbar, inline=False)

                    try:
                        add_list_embed_message.delete()
                    except:
                        pass
                    view = View(timeout=None)
                    view.add_item(PlayingButtonPrev(ctx, True if PlayList_count[ctx.channel.id] == 0 else False))
                    view.add_item(PlayingButtonPause(ctx))
                    view.add_item(PlayingButtonNext(ctx))
                    view.add_item(PlayingButtonStop(ctx))
                    repeat = PlayRepeat[ctx.channel.id]
                    repeat_label = "반복 재생 안함" if repeat == 0 else "반복 재생" if repeat == 1 else "한 곡 반복 재생"
                    repeat_style = discord.ButtonStyle.gray if repeat == 0 else discord.ButtonStyle.primary
                    view.add_item(PlayingButtonRepeat(ctx, repeat_label, repeat_style))
                    sendmessage = await ctx.send(embed=embedtitle, view=view)
                    #buttons_msg = await ctx.send("``buttons``", components=[action_row])
                    if len(SubtitleTexts[ctx.channel.id][0]) > 5:
                        await sendmessage.add_reaction("🇰🇷")
                    if len(SubtitleTexts[ctx.channel.id][1]) > 5:
                        await sendmessage.add_reaction("🇺🇸")
                    if len(SubtitleTexts[ctx.channel.id][2]) > 5:
                        await sendmessage.add_reaction("🇯🇵")
                    ctx.voice_client.play(player, after=await loding_video.delete())
                    ctx.voice_client.source.volume = NowVolumes[ctx.channel.id]
                    # 자막싱크 여기       ############################################################################################
                    await asyncio.sleep(0.5)
                    ############################################################################################
                    # if SubtitleTimes[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                    #    SubtitleCounts[ctx.channel.id]] == 9999:
                    #    await ctx.send("```자막이 없습니다!```", delete_after=20)

                    sleeptimefirst = t.time()
                    disposable = True
                    while_play[ctx.channel.id] = True
                    CheckStops[ctx.channel.id] = False

                    while while_play[ctx.channel.id]:
                        while PlayPauses[ctx.channel.id]:
                            # sleeptimefirst = t.time() - 1
                            await asyncio.sleep(0.1)
                        if CheckStops[ctx.channel.id]:
                            await sendmessage.delete()
                            #await buttons_msg.delete()
                            # await buttons_msg.edit(components=[])
                            if ThumbnailList[ctx.channel.id][PlayList_count[ctx.channel.id]] != "Null":
                                await sendembedthumbnail.delete()
                            CheckStops[ctx.channel.id] = False
                            SubtitleCounts[ctx.channel.id] = 0
                            for i in range(0, 3):
                                SubtitleTexts[ctx.channel.id][i].clear()
                                SubtitleTimes[ctx.channel.id][i].clear()
                            SubtitleNowTimes[ctx.channel.id] = 0
                            PlayList_count[ctx.channel.id] += 1
                            while_play[ctx.channel.id] = False
                            if PlayRepeat[ctx.channel.id] == 2:
                                PlayList_count[ctx.channel.id] -= 1
                            if PlayRepeat[ctx.channel.id] == 1 and PlayList_count[ctx.channel.id] == PlayList_max_count[ctx.channel.id]:
                                PlayList_count[ctx.channel.id] = 0

                            continue
                        if not SubtitleLanguageChangeCheck[ctx.channel.id]:
                            continue
                        sleeptime = 1

                        progressbarnowtimesecond = SubtitleNowTimes[ctx.channel.id] - (
                                math.floor(SubtitleNowTimes[ctx.channel.id] / 60) * 60)
                        if progressbarnowtimesecond < 10:
                            progressbarnowtimesecond = "0" + str(progressbarnowtimesecond)
                        progressbarnowtimeminute = str(math.floor(SubtitleNowTimes[ctx.channel.id] / 60))
                        progressbarnowtimesecond = str(progressbarnowtimesecond)

                        subtitle = "```yaml\n" + SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                            SubtitleCounts[ctx.channel.id]] + "\n```" + "```brainfuck\n" + \
                                   SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                       SubtitleCounts[ctx.channel.id] + 1] + "\n```"
                        # embedtitle.remove_field(1)
                        embedtitle.remove_field(0)

                        embedtitle.add_field(name="자막", value=subtitle, inline=False)

                        progressbardivision = player.duration / 30
                        progressbar = ""
                        progressbarfirstline = 0
                        if SubtitleNowTimes[ctx.channel.id] > progressbardivision:
                            progressbarfirstline = SubtitleNowTimes[ctx.channel.id] / progressbardivision

                        # for j in range(1, math.floor(progressbarfirstline)):
                        #    progressbar += "▬"
                        # progressbar += "🔘"
                        # for j in range(math.floor(progressbarfirstline), 30):
                        #    progressbar += "▬"
                        # embedtitle.add_field(name=str(progressbarnowtimeminute) + ":" + str(progressbarnowtimesecond) + " / " + str(total_minute) + ":" + str(total_second), value=progressbar, inline=False)

                        ####################################################
                        if SubtitleNowTimes[ctx.channel.id] >= \
                                SubtitleTimes[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                    SubtitleCounts[ctx.channel.id]]:
                            await  sendmessage.edit(embed=embedtitle)
                            # print(SubtitleCounts[ctx.channel.id])

                        if SubtitleNowTimes[ctx.channel.id] >= \
                                SubtitleTimes[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                    SubtitleCounts[ctx.channel.id]]:
                            subtitle = "```yaml\n" + \
                                       SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                           SubtitleCounts[ctx.channel.id] + 1] + "\n```" + "```brainfuck\n" + \
                                       SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                           SubtitleCounts[ctx.channel.id] + 2] + "\n```"
                            SubtitleCounts[ctx.channel.id] += 1
                        sleeptimesecond = t.time() - PauseSleep[ctx.channel.id]
                        sleepdelay = sleeptimesecond - sleeptimefirst
                        if sleepdelay > 1:
                            if sleepdelay > 2:
                                sleeptime = int(sleepdelay) + 1 - sleepdelay
                                for j in range(int(sleepdelay) - 1):
                                    SubtitleNowTimes[ctx.channel.id] += 1
                                    if SubtitleNowTimes[ctx.channel.id] >= \
                                            SubtitleTimes[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                                SubtitleCounts[ctx.channel.id]]:
                                        subtitle = "```yaml\n" + \
                                                   SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                                       SubtitleCounts[
                                                           ctx.channel.id] + 1] + "\n```" + "```brainfuck\n" + \
                                                   SubtitleTexts[ctx.channel.id][subtitletextlanguage[ctx.channel.id]][
                                                       SubtitleCounts[ctx.channel.id] + 2] + "\n```"
                                        SubtitleCounts[ctx.channel.id] += 1
                            else:
                                sleeptime -= sleepdelay - 1

                        else:
                            if disposable:
                                sleeptime = 0
                                disposable = False
                            else:
                                sleeptime += 1 - sleepdelay

                        # print(str(sleeptimefirst) + "/" + str(sleeptimesecond) + "/" + str(sleeptime) +
                        #      "/" + str(t.time()) + "/" + str(PauseSleep[ctx.channel.id]) + "/" + str(PauseSleep_t[ctx.channel.id]))
                        await asyncio.sleep(sleeptime)
                        sleeptimefirst = sleeptimesecond + sleeptime - 1
                        # sleeptimefirst = t.time() - 1

                        ## 노래가 끝날 때
                        if SubtitleNowTimes[ctx.channel.id] >= player.duration:
                            await sendmessage.delete()
                            # await buttons_msg.edit(components=[])
                            #await buttons_msg.delete()
                            if ThumbnailList[ctx.channel.id][PlayList_count[ctx.channel.id]] != "Null":
                                await sendembedthumbnail.delete()
                            SubtitleCounts[ctx.channel.id] = 0
                            for i in range(0, 3):
                                SubtitleTexts[ctx.channel.id][i].clear()
                                SubtitleTimes[ctx.channel.id][i].clear()
                            SubtitleNowTimes[ctx.channel.id] = 0
                            PlayList_count[ctx.channel.id] += 1
                            while_play[ctx.channel.id] = False
                            if PlayRepeat[ctx.channel.id] == 2:
                                PlayList_count[ctx.channel.id] -= 1
                            if PlayRepeat[ctx.channel.id] == 1 and PlayList_count[ctx.channel.id] == PlayList_max_count[ctx.channel.id]:
                                PlayList_count[ctx.channel.id] = 0
                        SubtitleNowTimes[ctx.channel.id] += 1

                if len(PlayLists[ctx.channel.id]) <= PlayList_count[ctx.channel.id]:
                    WhilePauses[ctx.channel.id] = False
        Playing[ctx.channel.id] = False
        # try:
        #     await ctx.voice_client.disconnect()
        #     await ctx.send("예약된 곡이 없어 종료합니다.", delete_after=5)
        # except:
        #     pass

    async def play_first(self, ctx, url):
        global DefaultVolume, CheckStops, SubtitleCounts, SubtitleTexts, SubtitleTimes, SubtitleLanguages, SubtitleNowTimes
        global ThumbnailList, WhilePauses, PlayLists, NowVolumes, PlayList_count, subtitletextlanguage, SubtitleLanguageChangeCheck
        global Playauthor, table_sql, PlayPauses, Ctx, PauseSleep, Playing

        conn = connInit()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            type(Playing[ctx.channel.id])
        except KeyError:
            Playing[ctx.channel.id] = False
        if Playing[ctx.channel.id]:
            # 배열이 있는지 확인
            self.check_variable(ctx)
            
            voice[ctx.guild.id] = ctx.channel
            CheckStops[ctx.channel.id] = False
            await self.add_list_emebed(ctx, url, cursor)

            if PlayList_ERROR[ctx.channel.id]:
                PlayList_ERROR[ctx.channel.id] = False
                return
        else:

            # 배열이 있는지 확인
            self.check_variable(ctx)
            # 배열 초기화
            try:
                ctx.voice_client.stop()
            except:
                pass
            voice[ctx.guild.id] = ctx.channel
            Playing[ctx.channel.id] = True
            WhilePauses[ctx.channel.id] = False
            CheckStops[ctx.channel.id] = True
            while_play[ctx.channel.id] = False
            Ctx[ctx.channel.id] = ctx
            PlayPauses[ctx.channel.id] = False
            PauseSleep[ctx.channel.id] = 0
            PauseSleep_t[ctx.channel.id] = 0
            PlayLists_title[ctx.channel.id].clear()
            await asyncio.sleep(0.1)
            SubtitleLanguageChangeCheck[ctx.channel.id] = True
            SubtitleCounts[ctx.channel.id] = 0
            PlayList_count[ctx.channel.id] = 0
            for i in range(0, 3):
                SubtitleTexts[ctx.channel.id][i].clear()
                SubtitleTimes[ctx.channel.id][i].clear()
            SubtitleNowTimes[ctx.channel.id] = 0
            PlayLists[ctx.channel.id].clear()
            ThumbnailList[ctx.channel.id].clear()
            Playauthor[ctx.channel.id].clear()
            # 플레이 리스트가 있을 경우 리스트 저장
            playlistfirst = 0
            playlistlast = 1
            que_txt = "```\n"
            que_txt2 = "```\n"
            que_chk = False

            add_list_embed_message = await self.add_list_emebed(ctx, url, cursor)
            if PlayList_ERROR[ctx.channel.id]:
                PlayList_ERROR[ctx.channel.id] = False
                return
            conn.close()
            # que_txt = que_txt + "```"
            # que_txt2 = que_txt2 + "```"
            # await ctx.send(content=que_txt, delete_after=20)
            # if que_chk:
            #    await ctx.send(content=que_txt2, delete_after=20)
            # 재생
            await self.player(ctx)

    @slash_command(name="재생", description="URL 노래를 재생목록에 추가한 뒤 재생합니다.")
    async def play(self, ctx, *, url:Option(str, "유튜브 URL또는 검색어를 입력하세요.")):

        if ctx.voice_client is None and not ctx.author.voice:
            return
        # if not (url.find("list=") != -1 or url.find("v=") != -1 or url.find("youtu.be/") != -1):
        #     embed = discord.Embed(title="오류!!", description="명령어 사용이 잘못됐습니다.", color=0xFF0000)
        #     embed.add_field(name="해결법", value="```!재생 유튜브링크```\n이 형식으로 재생하세요!", inline=False)
        #
        #     await ctx.send(embed=embed)
        #     return


        if not (url.find("list=") != -1 or url.find("v=") != -1 or url.find("youtu.be/") != -1):
            async with ctx.typing():
                await ctx.respond("검색을 시작합니다..", delete_after=5)
                try:
                    type(SearchingData[ctx.channel.id])
                except KeyError:
                    SearchingData[ctx.channel.id] = []
                await YTDLSource.from_title(ctx, url, loop=self.app.loop)
                embed_que = discord.Embed(title=SearchingData[ctx.channel.id][1], url="https://www.youtube.com/watch?v=" +
                                                                                      SearchingData[ctx.channel.id][0])
                embed_que.set_image(url="https://i.ytimg.com/vi/" + SearchingData[ctx.channel.id][0] + "/hqdefault.jpg")

                view = SearchButtons(self, ctx, SearchingData[ctx.channel.id])
                await ctx.send(embed=embed_que, view=view)

            return
        await self.play_first(ctx, url)


    # @que.error
    # @play.error
    # async def _play_error(self, ctx, error):
    #    if isinstance(error, commands.HTTPError):
    #        await ctx.send("테스트")

    async def add_list_emebed(self, ctx, url, cursor):
        chk = len(PlayLists[ctx.channel.id])
        await self.add_list(ctx, url, cursor)
        chk = len(PlayLists[ctx.channel.id]) - chk
        #print(url)
        if not (url.find("list=") != -1 or url.find("v=") != -1 or url.find("youtu.be/") != -1):
            pass
            # url = await self.search_urlid(url, cursor)
            # url = "https://www.youtube.com/watch?v=" + url
        if PlayList_ERROR[ctx.channel.id]:
            return
        # print(str(len(PlayLists[ctx.channel.id])) + " | " + str(chk))
        embed_que = discord.Embed(title=PlayLists_title[ctx.channel.id][len(PlayLists[ctx.channel.id]) - chk],
                                  url=url)
        embed_que.set_author(name="예약 　 　 　 　 　 　 　 　 　 　 　 　 　 　")
        embed_que.add_field(name="예약 성공!", value=str(
            len(PlayLists[ctx.channel.id]) - chk - int(PlayList_count[ctx.channel.id])) +
                                                 "번째에 재생됩니다.", inline=True)
        embed_que.add_field(name="예약 항목 수", value=str(chk), inline=True)
        if ThumbnailList[ctx.channel.id][len(PlayLists[ctx.channel.id]) - chk] != "Null":
            embed_que.set_image(url=ThumbnailList[ctx.channel.id][len(PlayLists[ctx.channel.id]) - chk])
        return await ctx.send(embed=embed_que, delete_after=5)

    async def add_list(self, ctx, url, cursor):
        global url_id
        await ctx.respond("등록 준비..", delete_after=1)
        loding_list = await ctx.send("``플레이리스트 불러오는 중..``")
        if url.find("list=") != -1:
            chk = False
            playlisturlsplit = url.split("list=")
            url_id = ""
            if url.find("v=") != -1:
                test = url.split("v=")
                for i in range(0, 11):
                    url_id += test[1][i]
            else:
                test = url.split("youtu.be/")
                for i in range(0, 11):
                    url_id += test[1][i]

            playlisturl = urllib.request.urlopen(
                "https://www.googleapis.com/youtube/v3/playlistItems?" +
                "part=snippet&maxResults=50&key=AIzaSyDEfBsMmcstsyfWkA_32IKWDoiOKmppWkQ&playlistId=" +
                playlisturlsplit[1]).read()
            playlistjson = json.loads(playlisturl)
            playlistfirst = 0
            playlistlast = int(playlistjson["pageInfo"]["totalResults"])
            try:
                nextPageToken = playlistjson["nextPageToken"]
            except KeyError:
                nextPageToken = "Null"
            while_playlist_count = 0
            while_playlist_MAX = 1
            forcedExit = 0
            chk = False
            while True:
                forcedExit += 1
                if forcedExit > 20:
                    await ctx.send("``재생목록을 추가하지 못했습니다. 다른 URL을 입력해 주세요.``")
                    await loding_list.delete()
                    PlayList_ERROR[ctx.channel.id] = True
                    return
                if playlistlast < while_playlist_count:
                    break
                if while_playlist_MAX != 1:
                    # if nextPageToken == "Null":
                    #    await ctx.send("``재생목록을 추가하지 못했습니다. 다른 URL을 입력해 주세요.``")
                    #    await loding_list.delete()
                    #    PlayList_ERROR[ctx.channel.id] = True
                    #    return
                    if nextPageToken == "Null":
                        break
                    playlisturl = urllib.request.urlopen(
                        "https://www.googleapis.com/youtube/v3/playlistItems?" +
                        "part=snippet&maxResults=50&key=AIzaSyDEfBsMmcstsyfWkA_32IKWDoiOKmppWkQ&playlistId=" +
                        playlisturlsplit[1] + "&pageToken=" + nextPageToken).read()
                    playlistjson = json.loads(playlisturl)
                    try:
                        nextPageToken = playlistjson["nextPageToken"]
                    except KeyError:
                        nextPageToken = "Null"
                for i in range(playlistfirst, playlistlast):
                    while_playlist_count += 1
                    if playlistlast < while_playlist_count or i >= 50:
                        while_playlist_count -= 1
                        break
                    # if len(que_txt + str(i + 1) + ". " + playlistjson['items'][i]['snippet']['title'] + "\n") >= 2000:
                    #    que_chk = True
                    #    que_txt2 = que_txt2 + str(i + 1) + ". " + playlistjson['items'][i]['snippet']['title'] + "\n"
                    # else:
                    #    que_txt = que_txt + str(i + 1) + ". " + playlistjson['items'][i]['snippet']['title'] + "\n"
                    # print(str(while_playlist_count) + " | " + str(playlistlast) + " | " + str(i) + " | " + str(while_playlist_MAX))
                    if url_id == playlistjson['items'][i]['snippet']['resourceId']['videoId']:
                        chk = True
                    if chk:
                        result = await self.find_table(playlistjson['items'][i]['snippet']['resourceId']['videoId'],
                                                       cursor)
                        if result == 0:
                            cursor.execute(
                                table_sql_title_insert,
                                (
                                    playlistjson['items'][i]['snippet']['videoOwnerChannelTitle'],
                                    playlistjson["items"][i]["snippet"]["title"],
                                    "https://i.ytimg.com/vi/" + playlistjson['items'][i]['snippet']['resourceId'][
                                        'videoId'] +
                                    "/hqdefault.jpg",
                                    playlistjson['items'][i]['snippet']['resourceId']['videoId']
                                )
                            )
                            await self.insert_quantity(cursor,
                                                       playlistjson['items'][i]['snippet']['videoOwnerChannelTitle'])
                            await self.select_table(ctx, playlistjson['items'][i]['snippet']['resourceId']['videoId'],
                                                    cursor)
                        else:
                            await self.select_table(ctx, playlistjson['items'][i]['snippet']['resourceId']['videoId'],
                                                    cursor)
                # print(str(i) + " | " + nextPageToken + " | " + str(chk))

                if playlistlast > 50:
                    while_playlist_MAX = math.ceil(playlistlast / 50)



        else:
            url_id = ""
            if url.find("v=") != -1:
                test = url.split("v=")
                for i in range(0, 11):
                    url_id += test[1][i]
            elif url.find("youtu.be/") != -1:
                test = url.split("youtu.be/")
                for i in range(0, 11):
                    url_id += test[1][i]

            if url_id != "":
                result = await self.find_table(url_id, cursor)
                if result == 0:
                    await self.insert_table_bool(ctx, url_id, cursor)
                else:
                    await self.select_table(ctx, url_id, cursor)
            else:
                pass
                # url_id = url
                # cursor.execute(search_sql, url_id)
                # result = cursor.fetchone()
                # result = result['count(url_id)']
                # if result == 0:
                #
                #     try:
                #         data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?q=" +
                #                                       url_id + "&videoCaption=any&type=video&part=snippet" +
                #                                       "&key=AIzaSyDEfBsMmcstsyfWkA_32IKWDoiOKmppWkQ&maxResults=1"
                #                                       ).read()
                #     except:
                #         await loding_list.delete()
                #         await ctx.send("``YouTube 검색 Api 할당량이 초과되어 검색어로 재생하지 못했습니다.\n"
                #                        "!재생 {URL} 형식으로 명령어를 실행하세요.``", delete_after=10)
                #         #return
                #     datajson = json.loads(data)
                #     # url_id = datajson["items"][0]["id"]["videoId"]
                #     cursor.execute(search_sql_insert,
                #                    (datajson["items"][0]["id"]["videoId"],
                #                     url_id))
                #     url_id = datajson["items"][0]["id"]["videoId"]
                #     result = await self.find_table(url_id, cursor)
                #     if result == 0:
                #         await self.insert_table(ctx, url_id, cursor, datajson)
                #     else:
                #         await self.select_table(ctx, url_id, cursor)
                # else:
                #     url_id = await self.search_urlid(url_id, cursor)
                #     result = await self.find_table(url_id, cursor)
                #     if result == 0:
                #         await self.insert_table_bool(ctx, url_id, cursor)
                #     else:
                #         await self.select_table(ctx, url_id, cursor)
        await loding_list.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        global SubtitleLanguageChangeCheck
        # print(str(user.id) + "          " + str(Playauthor[reaction.message.channel.id]))
        if user.bot == 1:  # 봇이면 패스
            return None
        try:
            if str(user.id) != str(
                    Playauthor[reaction.message.channel.id][PlayList_count[reaction.message.channel.id] - 1]):
                return None
        except KeyError:
            return None

        SubtitleLanguageChangeCheck[reaction.message.channel.id] = False
        SubtitleCounts[reaction.message.channel.id] = 0
        if str(reaction.emoji) == "🇰🇷":
            subtitletextlanguage[reaction.message.channel.id] = 0
            for i in range(0, len(SubtitleTexts[reaction.message.channel.id][0]) - 1):
                if SubtitleTimes[reaction.message.channel.id][0][i] > SubtitleNowTimes[reaction.message.channel.id]:
                    SubtitleLanguageChangeCheck[reaction.message.channel.id] = True
                    return None
                else:
                    SubtitleCounts[reaction.message.channel.id] += 1

        elif str(reaction.emoji) == "🇺🇸":
            subtitletextlanguage[reaction.message.channel.id] = 1
            for i in range(0, len(SubtitleTexts[reaction.message.channel.id][1]) - 1):
                if SubtitleTimes[reaction.message.channel.id][1][i] > SubtitleNowTimes[reaction.message.channel.id]:
                    SubtitleLanguageChangeCheck[reaction.message.channel.id] = True
                    return None
                else:
                    SubtitleCounts[reaction.message.channel.id] += 1
        elif str(reaction.emoji) == "🇯🇵":
            subtitletextlanguage[reaction.message.channel.id] = 2
            for i in range(0, len(SubtitleTexts[reaction.message.channel.id][2]) - 1):
                if SubtitleTimes[reaction.message.channel.id][2][i] > SubtitleNowTimes[reaction.message.channel.id]:
                    SubtitleLanguageChangeCheck[reaction.message.channel.id] = True
                    return None
                else:
                    SubtitleCounts[reaction.message.channel.id] += 1

    @play.before_invoke
    @playlist.before_invoke
    @myplaylist.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                self.check_variable(ctx)
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("음성 채널에 연결되어 있지 않습니다.")
                # raise commands.CommandError("작성자가 음성 채널에 연결되지 않았습니다.")
        # elif ctx.voice_client.is_playing():
        #    ctx.voice_client.stop()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            # 음성 채널에서 나가는 경우
            if before.channel is not None and after.channel is None:
                for channel in member.guild.text_channels:
                    if voice[member.guild.id].id == channel.id:
                        if len(before.channel.members) == 1:  # 현재 음성 채널에 봇을 제외한 멤버가 없는 경우
                            await self.stop(Ctx[channel.id])
        except:
            pass


    def check_variable(self, ctx):
            try:
                type(voice[ctx.channel.id])
                type(CheckStops[ctx.channel.id])
                type(SubtitleCounts[ctx.channel.id])
                type(SubtitleTexts[ctx.channel.id])
                type(SubtitleTimes[ctx.channel.id])
                type(SubtitleNowTimes[ctx.channel.id])
                type(ThumbnailList[ctx.channel.id])
                type(WhilePauses[ctx.channel.id])
                type(PlayLists[ctx.channel.id])
                type(NowVolumes[ctx.channel.id])
                type(PlayLists_title[ctx.channel.id])
                type(PlayList_count[ctx.channel.id])
            except KeyError:
                voice[ctx.channel.id] = None
                CheckStops[ctx.channel.id] = False
                SubtitleCounts[ctx.channel.id] = []
                SubtitleNowTimes[ctx.channel.id] = []
                SubtitleTexts[ctx.channel.id] = []
                SubtitleTimes[ctx.channel.id] = []
                ThumbnailList[ctx.channel.id] = []
                WhilePauses[ctx.channel.id] = True
                PlayLists[ctx.channel.id] = []
                NowVolumes[ctx.channel.id] = DefaultVolume
                PlayLists_title[ctx.channel.id] = []
                PlayList_count[ctx.channel.id] = 0
                SubtitleLanguageChangeCheck[ctx.channel.id] = True
                Playauthor[ctx.channel.id] = []
                PauseSleep[ctx.channel.id] = 0
                PauseSleep_t[ctx.channel.id] = 0
                Playing[ctx.channel.id] = False
                PlayList_ERROR[ctx.channel.id] = False
                SubtitleTitle[ctx.channel.id] = []
                PlayRepeat[ctx.channel.id] = 0
                PlayList_max_count[ctx.channel.id] = 0

                for i in range(0, 3):
                    SubtitleTexts[ctx.channel.id].append([i])
                    SubtitleTimes[ctx.channel.id].append([i])
                    SubtitleTitle[ctx.channel.id].append([i])
