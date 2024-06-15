from discord.ext import commands
from discord.commands import slash_command, Option
from discord.ui import Select, View, Button
import discord
from yt_dlp import YoutubeDL
import asyncio
import json
import time as tt
from requests import Session
import re
from utils.error import CustomError

guilds = {}

SubtitleLanguages = ["ko", "en", "ja"]

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

ydl = YoutubeDL(ytdl_format_options)

def setup(app):
    app.add_cog(Core(app))

    
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    def from_url(cls, url, *, stream=False):
        print(1)
        # loop = loop or asyncio.get_event_loop()
        print(2)
        # def download_and_process():
        print(3)
        data = ydl.extract_info(url, download=not stream)
        print(4)
        if 'entries' in data:
            print(5)
            data = data['entries'][0]
        print(6)
        filename = data['url'] if stream else ydl.prepare_filename(data)
        print(7)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        
        # return await loop.run_in_executor(None, lambda: download_and_process())

    # @classmethod
    # async def from_url(cls, url, *, loop=None, stream=False):
    #     loop = loop or asyncio.get_event_loop()

    #     data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
    #     if 'entries' in data:
    #         data = data['entries'][0]
            
    #     filename = data['url'] if stream else ydl.prepare_filename(data)

    #     return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        

class Music():
    def __init__(self, loop):
        self.loop = loop
        self.music_loop = False # 반복재생 여부
        self.playing = False # 재생중 여부
        self.subtitles = [] # 자막 - [{title: 제목, subtitles: [{언어: 언어코드, 자막: [{text: 자막, time: 시간}]}, ...]}]
        self.subtitles_index = 0 # 자막 인덱스
        self.subtitles_language = "ko" # 자막 언어
        self.current = 0 # 현재 재생중인 음악 - 인덱스
        self.player = [] # 음악 플레이어 - discord.FFmpegPCMAudio
        self.volume = 0.1 # 볼륨
        self.now_time = 0 # 현재 재생 시간

    async def queue(self, ctx, url):
        test = await ctx.send("로딩중...")
        check_player = False
        
        for p in self.player:
            if p.data.get('webpage_url').split("v=")[1] == url.split("v=")[1].split("&")[0]:
                check_player = True
                self.player.append(p)
                self.subtitles.append(subtitle for subtitle in self.subtitles if subtitle['title'] == p.title)
                break
        if not check_player:
            try:
                data = await self.loop.run_in_executor(None, YTDLSource.from_url, url)
            except Exception as e:
                raise CustomError(f"다운로드 중 오류가 발생했습니다. {e}")
            try:
                await self.import_subtitles(data.data)
            except Exception as e:
                raise CustomError(f"자막 다운로드 중 오류가 발생했습니다. {e}")
            self.player.append(data)
        try:
            await test.delete()
        except:
            pass
        await ctx.send("재생목록에 추가되었습니다.", delete_after=5)
        if not self.playing:
            await self.play(ctx)

    async def import_subtitles(self, info):
        clean = '<.*?>'
        subtitles_temp = {'title': info.get('title'), 'subtitles': []}
        has_subtitles = False
        f_t = tt.time()
        with Session() as session:
            print(len(info.get('subtitles', {})))
            for k, subtitles_list in info.get('subtitles', {}).items():
                if '-' in k and len(k.split('-')[1]) > 2:
                    continue
                has_subtitles = True
                subtitles_lang_temp = {'lang': k, 'subtitles': []}
                url = [item['url'] for item in subtitles_list if item['ext'] == 'vtt']
                t_t = tt.time()
                f = re.sub(clean, '', session.get(url[0]).text).replace("\u200b", "")
                print("언어: " + k + " - " + str(tt.time() - t_t) + "초 걸림")
                lines = f.splitlines()

                tempTimes = []
                tempSubtiles = []
                chk = False
                timeChk = True
                for line in lines:
                    if line == "\n" or line == "":
                        continue
                    if timeChk:
                        if '-->' not in line:
                            continue
                        else:
                            timeChk = False


                    if '-->' in line:
                        #time
                        h = line[0:2]
                        m = line[3:5]
                        s = line[6:8]
                        t = line[9:10]
                        time = float(str(int(h) * 360 + int(m) * 60 + int(s)) + "." + t)
                        if len(tempTimes) == 0 or time - tempTimes[-1] > 1:
                            tempTimes.append(time)
                            chk = True
                        else:
                            chk = False

                    else:
                        #subtitle
                        if chk:
                            tempSubtiles.append(line)

                        else:
                            tempSubtiles[-1] += "\n" + line

                tempSubtiles.insert(0, " ")
                tempSubtiles.append(" ")
                tempTimes.append(99999)
                tempTimes.append(99999)
                print(len(tempSubtiles), len(tempTimes))
                for i in range(len(tempTimes)):
                    subtitles_lang_temp.get('subtitles').append({'text': tempSubtiles[i], 'time': tempTimes[i]})
                subtitles_temp.get('subtitles').append(subtitles_lang_temp)
        if has_subtitles:
            self.subtitles.append(subtitles_temp)
        print("총 " + str(tt.time() - f_t) + "초 걸림")


    async def play(self, ctx):
        if self.playing:
            return
        if len(self.player) == 0:
            return
        
        self.playing = True
        while self.current < len(self.player):
            self.subtitles_index = 0
            self.now_time = 0
            ctx.voice_client.play(self.player[self.current])

            current_subtitles = next((subtitle for subtitle in self.subtitles if subtitle['title'] == self.player[self.current].title), None)
            # 재생 중인 음악 정보 출력
            embedtitle = discord.Embed(title=self.player[self.current].title, url=self.player[self.current].data.get('webpage_url'))
            embedtitle.set_author(name="현재 재생중~")
            embedtitle.set_image(url=self.player[self.current].data.get('thumbnail'))
            sendmessage = await ctx.send(embed=embedtitle)



            subtitle_change = True
            message = ""
            subtitle_current_lang = self.subtitles_language
            subtitle = next((sub for sub in current_subtitles['subtitles'] if sub['lang'] == self.subtitles_language), current_subtitles['subtitles'][0])
            # await asyncio.sleep(5)
            first_time = tt.time() # 코드 걸린 시간을 포함해서 1초를 쉬기 위한 변수
            self.now_time = first_time - 1

            while ctx.voice_client.is_playing(): # 음악이 재생중일 때
                if ctx.voice_client.is_paused(): # 음악이 일시정지 상태일 때
                    await asyncio.sleep(0.1) 
                    continue
                time = tt.time() - self.now_time
                for i in range(self.subtitles_index, len(subtitle['subtitles'])):
                    if time >= subtitle['subtitles'][i]['time']:
                        self.subtitles_index += 1
                        subtitle_change = True
                        break

                # 자막 출력
                if current_subtitles and subtitle_change:
                    subtitle_change = False
                    print("change")
                    

                    # TODO: 자막 언어 바뀔 때만 작동하도록 수정
                    if subtitle_current_lang != self.subtitles_language:
                        self.subtitles_language = subtitle_current_lang
                        subtitle = next((sub for sub in current_subtitles['subtitles'] if sub['lang'] == self.subtitles_language), current_subtitles['subtitles'][0]) 
                    
                    embedtitle.remove_field(0)
                    message = f"```yaml\n{subtitle['subtitles'][self.subtitles_index]['text']}\n```"

                    if len(subtitle['subtitles']) > self.subtitles_index + 1:
                        message += f"```brainfuck\n{subtitle['subtitles'][self.subtitles_index + 1]['text']}\n```"
                    else:
                        message += "```brainfuck\n End \n ```"
                    embedtitle.add_field(name="자막", value=message, inline=False)
                    await sendmessage.edit(embed=embedtitle)
                




                
                # second_time = t.time()

                # delay = second_time - first_time

                # if delay > 1:
                #     await asyncio.sleep(delay)
                # else:
                #     await asyncio.sleep(1-delay)
                await asyncio.sleep(0.5)
                # first_time = second_time + delay
                # print(delay)

            self.current += 1

            # Exception in voice thread Thread-4
            # Traceback (most recent call last):
            # File "C:\Users\akso6\AppData\Local\Programs\Python\Python312\Lib\site-packages\discord\player.py", line 756, in run
            #     self._do_run()
            # File "C:\Users\akso6\AppData\Local\Programs\Python\Python312\Lib\site-packages\discord\player.py", line 743, in _do_run
            #     data = self.source.read()
            #         ^^^^^^^^^^^^^^^^^^
            # File "C:\Users\akso6\AppData\Local\Programs\Python\Python312\Lib\site-packages\discord\player.py", line 695, in read
            #     ret = self.original.read()
            #         ^^^^^^^^^^^^^^^^^^^^
            # File "C:\Users\akso6\AppData\Local\Programs\Python\Python312\Lib\site-packages\discord\player.py", line 316, in read
            #     ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
            #         ^^^^^^^^^^^^^^^^^

        self.playing = False



guild_ids = ["1016514629603700766","537629446878920733","888048290141179934"]

class Core(commands.Cog, name="뮤직봇"):

    def __init__(self, app):
        self.app = app
        self.loop = app.loop

    @slash_command(name="join", description="음성 채널에 봇을 초대합니다.", guild_ids=guild_ids)
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("음성 채널에 먼저 들어가주세요.")
            return
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        await ctx.author.voice.channel.connect()
        await ctx.send("음성 채널에 입장했습니다.")

    @slash_command(name="leave", description="음성 채널에서 봇을 퇴장시킵니다.")
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("음성 채널에 봇이 없습니다.")
            return
        await ctx.voice_client.disconnect()
        await ctx.send("음성 채널에서 퇴장했습니다.")

    @slash_command(name="play", description="음악을 재생합니다.", guild_ids=guild_ids)
    async def play(self, ctx, url: str):
        
        if not guilds.get(ctx.guild.id):
            guilds[ctx.guild.id] = Music(self.loop)

        await guilds[ctx.guild.id].queue(ctx, url)
        
    
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:  # 채널에 들어가 있는지 파악
            # 봇이 다른 음성채널에 들어가 있고, 유저와 같은 채널이 아닐 경우
            if ctx.voice_client and ctx.voice_client.channel and ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
                await ctx.respond("음성채널을 옮겼습니다.", delete_after=5)
            elif not ctx.voice_client:  # 봇이 음성채널에 없을 경우
                channel = ctx.author.voice.channel  # 채널 구하기
                await channel.connect()  # 채널 연결
                await ctx.respond("봇이 음성채널에 입장했습니다.", delete_after=5)
        else:  # 유저가 채널에 없으면
            await ctx.respond("음성채널에 연결되지 않았습니다.", delete_after=5)  # 출력
    # @commands.Cog.listener()
    # async def check_guilds(self, ctx):
    #     if not guilds.get(ctx.guild.id):
    #         guilds[ctx.guild.id] = Music()
        