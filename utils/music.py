from discord import Embed
import discord
import asyncio
import time as tt
from utils.error import CustomError
from utils.view import SearchView, playControlPanel, ListView
from utils.youtube import YTDLSource
from utils.subtitle import Subtitle

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

    def reset(self):
        self.music_loop = False
        self.playing = False
        self.subtitles = []
        self.subtitles_index = 0
        self.subtitles_language = "ko"
        self.current = 0
        self.player = []
        self.now_time = 0

    async def download(self, ctx, url):
        check_player = False
        # for p in self.player:
        #     if p.data.get('webpage_url').split("v=")[1] == url.split("v=")[1].split("&")[0]:
        #         check_player = True
        #         self.player.append(p)
        #         self.subtitles.append(subtitle for subtitle in self.subtitles if subtitle['title'] == p.title)
        #         break
        if not check_player:
            try:
                data = await self.loop.run_in_executor(None, YTDLSource.from_url, url)
            except Exception as e:
                raise CustomError(f"다운로드 중 오류가 발생했습니다. {e}")
            try:
                sub = await Subtitle.import_subtitles(data.data)
                if sub:
                    self.subtitles.append(sub)
            except Exception as e:
                raise CustomError(f"자막 다운로드 중 오류가 발생했습니다. {e}")
            try:
                data.data['author'] = ctx.author.global_name
            except:
                data.data['author'] = ctx.user.global_name
            self.player.append(data)

    async def search(self, ctx, query):
        if ctx.response.is_done():
            await ctx.edit(content="검색중...")
        else:
            await ctx.respond("검색중...")
        data = await YTDLSource.from_title(query)
        if data == 1:
            await ctx.edit(content="``재생 목록을 불러오지 못했어요..!!``", delete_after=10)
            return
        embed = Embed(title=data[1], url=f"https://www.youtube.com/watch?v={data[0]}")
        embed.set_image(url=f"https://i.ytimg.com/vi/{data[0]}/hqdefault.jpg")
        view = SearchView(ctx, data, self)
        await ctx.edit(content="", view=view, embed=embed)
        # await view.init(await ctx.interaction.original_message().id)

    async def list(self, ctx, url, current=False, msg=None):
        
        urltemp = f'https://music.youtube.com/playlist?list={url.split("list=")[1]}'
        data = await YTDLSource.from_list(urltemp)
        if data == 1:
            await ctx.edit(content="``재생 목록을 불러오지 못했어요..!!``", delete_after=10)
            return
        if current:
            for i in range(0, len(data), 2):
                if url.split("v=")[1].split("&")[0] == data[i]:
                    data = data[i:]
                    break
        for i in range(0, len(data), 2):
            data[i] = f"https://www.youtube.com/watch?v={data[i]}"
        await self.list_queue(ctx, data, msg=msg)

    async def list_queue(self, ctx, url, msg=None):
        if msg:
            await msg.edit(content="로딩중...", view=None, embed=None)
        else:
            test = await ctx.send(f"로딩중... (0/{int(len(url) / 2)})")
        
        time = tt.time()

        for i in range(0, len(url), 2):
            await self.download(ctx, url[i])
            if tt.time() - time > 1:
                time = tt.time()
                if msg:
                    await msg.edit(f"로딩중... ({int(i/2+1)}/{int(len(url) / 2)})")
                else:
                    await test.edit(f"로딩중... ({int(i/2+1)}/{int(len(url) / 2)})")
            if not self.playing:
                asyncio.create_task(self.play(ctx))
                

        if msg:
            await msg.edit(content=f"{int(len(url) / 2)}개의 곡이 재생목록에 추가되었습니다.", delete_after=5)
        else:
            await test.edit(f"{int(len(url) / 2)}개의 곡이 재생목록에 추가되었습니다.", delete_after=5)

        if not self.playing:
            await self.play(ctx)

    async def queue(self, ctx, url, msg=None):
        if msg:
            await msg.edit(content="로딩중...", view=None, embed=None)
        else:
            test = await ctx.send("로딩중...")

        await self.download(ctx, url)

        if msg:
            try:
                await msg.edit(content="재생목록에 추가되었습니다.", delete_after=5)
            except:
                await msg.edit(content="재생목록에 추가되었습니다.")
                tt.sleep(5)
                await msg.delete()
        else:
            await test.edit("재생목록에 추가되었습니다.", delete_after=5)

        if not self.playing:
            await self.play(ctx)


    async def play(self, ctx):
        if self.playing:
            return
        if len(self.player) == 0:
            return
        
        self.playing = True
        while self.current < len(self.player):
            try:
                self.subtitles_index = 0
                self.now_time = 0
                try:
                    current_subtitles = next((subtitle for subtitle in self.subtitles if subtitle['title'] == self.player[self.current].title), None)
                except:
                    current_subtitles = None
                # 재생 중인 음악 정보 출력
                embedtitle = discord.Embed(title=self.player[self.current].title, url=self.player[self.current].data.get('webpage_url'))
                embedtitle.set_author(name="현재 재생중~")
                embedtitle.set_image(url=self.player[self.current].data.get('thumbnail'))
                embedtitle.add_field(name="요청자", value="``" + self.player[self.current].data.get('author') + "``", inline=True)
                # 다음곡
                if self.current + 1 < len(self.player):
                    embedtitle.add_field(name="다음곡", value="``" + self.player[self.current + 1].title + "``", inline=True)
                else:
                    embedtitle.add_field(name="다음곡", value="``없음``", inline=True)
                sendmessage = await ctx.send(embed=embedtitle, view=playControlPanel(ctx, self))

                language_reactions = {
                    'ko': "🇰🇷",
                    'en': "🇺🇸",
                    'ja': "🇯🇵",
                    'zh-CN': "🇨🇳",
                    'zh-TW': "🇹🇼"
                }
                for sub in current_subtitles.get('subtitles', []):
                    lang = sub.get('lang')
                    if lang in language_reactions:
                        await sendmessage.add_reaction(language_reactions[lang])

                ctx.voice_client.play(self.player[self.current])


                subtitle_change = True
                message = ""
                subtitle_current_lang = self.subtitles_language
                # print(f".{current_subtitles}.")
                subtitle = None
                if current_subtitles:
                    subtitle = next((sub for sub in current_subtitles['subtitles'] if sub['lang'] == self.subtitles_language), current_subtitles['subtitles'][0] )
                # await asyncio.sleep(5)
                first_time = tt.time() # 코드 걸린 시간을 포함해서 1초를 쉬기 위한 변수
                self.now_time = first_time - 1

                while True: # 음악이 재생중일 때
                    if not ctx.voice_client:
                        break
                    if not ctx.voice_client.is_playing(): # 음악이 재생중이지 않을 때
                        break
                    if ctx.voice_client.is_paused(): # 음악이 일시정지 상태일 때
                        await asyncio.sleep(0.1) 
                        continue
                    time = tt.time() - self.now_time
                    if subtitle:
                        if subtitle_current_lang != self.subtitles_language:
                            self.subtitles_index = 0
                            subtitle_change = True
                            subtitle_current_lang = self.subtitles_language
                            subtitle = next((sub for sub in current_subtitles['subtitles'] if sub['lang'] == self.subtitles_language), current_subtitles['subtitles'][0]) 
                        for i in range(self.subtitles_index, len(subtitle['subtitles'])):
                            if time >= subtitle['subtitles'][i]['time']:
                                self.subtitles_index += 1
                                subtitle_change = True
                    
                    embedtitle.clear_fields()
                    embedtitle.add_field(name="요청자", value="``" + self.player[self.current].data.get('author') + "``", inline=True)
                    # 다음곡
                    if self.current + 1 < len(self.player):
                        embedtitle.add_field(name="다음곡", value="``" + self.player[self.current + 1].title + "``", inline=True)
                    else:
                        embedtitle.add_field(name="다음곡", value="``없음``", inline=True)
                    # 자막 출력
                    if subtitle:
                        if current_subtitles and subtitle_change:
                            subtitle_change = False
                            
                            message = f"```yaml\n{subtitle['subtitles'][self.subtitles_index]['text']}\n```"

                            if len(subtitle['subtitles']) > self.subtitles_index + 1:
                                message += f"```brainfuck\n{subtitle['subtitles'][self.subtitles_index + 1]['text']}\n```"
                            else:
                                message += "```brainfuck\n End \n ```"
                            embedtitle.add_field(name="자막", value=message[:900], inline=False)
                            await sendmessage.edit(embed=embedtitle)
                    else:
                        await asyncio.sleep(0.5)
                        await sendmessage.edit(embed=embedtitle)
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(e)
                ctx.voice_client.stop()
                try:
                    await sendmessage.delete()
                except:
                    pass
                await ctx.send("오류가 발생하여 이번 곡을 정지합니다.")
            self.current += 1
            try:
                await sendmessage.delete()
            except:
                pass

        self.playing = False

    async def commandPlay(self, ctx, url):
        # URL이 아닐 경우
        if not url.startswith("http"):
            await self.search(ctx, url)
            return
        # 잘못된 URL
        elif not (url.startswith("https://www.youtube.com/") or \
            url.startswith("https://youtu.be/") or \
            url.startswith("https://youtube.com/") or \
            url.startswith("https://music.youtube.com/") or \
            url.startswith("https://m.youtube.com/")):
            raise CustomError("유튜브 URL이 아닙니다.")
        elif "list=" in url:
            view = ListView(ctx, self, url)
            msg = await ctx.send("재생목록을 발견했습니다. 추가할 방법을 선택해주세요.", view=view)
            view.init(msg)
        else:
            await self.queue(ctx, url)

    async def commandSkip(self, ctx):
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if not ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있지 않습니다.")
        ctx.voice_client.stop()
        await ctx.respond("음악을 건너뛸게요.", delete_after=5)

    async def commandStop(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("음성 채널에 봇이 없습니다.")
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            self.reset()
        await ctx.voice_client.disconnect()
        await ctx.respond("음성 채널에서 퇴장했습니다.")