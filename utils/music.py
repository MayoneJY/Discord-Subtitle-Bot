from discord import Embed
import discord
import asyncio
import time as tt
from utils.error import CustomError
from utils.view import SearchView, playControlPanel, ListView
from utils.youtube import YTDLSource
from utils.subtitle import Subtitle
from datetime import datetime

class Music():
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop
        self.music_loop = "안함" # 반복재생 여부
        self.playing = False # 재생중 여부
        self.subtitles = [] # 자막 - [{title: 제목, subtitles: [{언어: 언어코드, 자막: [{text: 자막, time: 시간}]}, ...]}]
        self.subtitles_index = 0 # 자막 인덱스
        self.subtitles_language = "ko" # 자막 언어
        self.current = 0 # 현재 재생중인 음악 - 인덱스
        self.player = [] # 음악 플레이어 - discord.FFmpegPCMAudio
        self.volume = 0.1 # 볼륨
        self.now_time = 0 # 현재 재생 시간
        self.pasue_time = 0

    def reset(self):
        self.music_loop = "안함"
        self.playing = False
        self.subtitles = []
        self.subtitles_index = 0
        self.subtitles_language = "ko"
        self.current = 0
        self.player = []
        self.now_time = 0
        self.pasue_time = 0

    async def download(self, ctx, url):
        download_msg = await ctx.send("다운로드 중...")
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
            # try:
            #     data.data['author'] = ctx.author.global_name
            # except:
            #     data.data['author'] = ctx.user.global_name
            # self.player.append(data)
            await download_msg.delete()
            return data

    async def search(self, ctx, query):
        if ctx.response.is_done():
            await ctx.edit(content="검색중...")
        else:
            await ctx.respond("검색중...")
        data = await YTDLSource.from_title(query, author=ctx.user.global_name)
        if data == 1:
            await ctx.edit(content="``재생 목록을 불러오지 못했어요..!!``", delete_after=10)
            return
        embed = Embed(title=data['title'][0], url=data['url'][0])
        embed.set_image(url=data['thumbnail'][0])
        embed.set_footer(text=data['duration'][0])
        view = SearchView(ctx, data, self)
        await ctx.edit(content="", view=view, embed=embed)
        # await view.init(await ctx.interaction.original_message().id)

    async def list(self, ctx, url, current=False, msg=None):
        
        urltemp = f'https://music.youtube.com/playlist?list={url.split("list=")[1]}'
        data = await YTDLSource.from_list(urltemp, author=ctx.user.global_name)
        if data == 1:
            await ctx.edit(content="``재생 목록을 불러오지 못했어요..!!``", delete_after=10)
            return
        if current:
            for i in range(len(data['url'])):
                if url.split("v=")[1].split("&")[0] == data['url'][i].split("v=")[1]:
                    data['url'] = data['url'][i:]
                    data['title'] = data['title'][i:]
                    data['thumbnail'] = data['thumbnail'][i:]
                    data['author'] = data['author'][i:]
                    break
        

        await self.list_queue(ctx, data, msg=msg)

    async def list_queue(self, ctx, url, msg=None):
        if msg:
            await msg.edit(content="로딩중...", view=None, embed=None)
        else:
            if ctx.response.is_done():
                await ctx.edit(content="로딩중...")
            else:
                await ctx.respond("로딩중...")
        
        for i in range(len(url['url'])):
            self.player.append({'url': url['url'][i], 'title': url['title'][i], 'thumbnail': url['thumbnail'][i], 'author': url['author'][i]})

        if msg:
            await self.queue_embed(msg, url)
        else:
            await self.queue_embed(ctx, url)

        if not self.playing:
            await self.play(ctx)

    async def queue(self, ctx, url, msg=None):
        if msg:
            await msg.edit(content="로딩중...", view=None, embed=None)
        else:
            if ctx.response.is_done():
                await ctx.edit(content="로딩중...")
            else:
                await ctx.respond("로딩중...")

        # await self.download(ctx, url)
        player = await YTDLSource.from_title_solo(url, author=ctx.user.global_name)
        if player == 1:
            await ctx.delete()
            raise CustomError("음악을 추가하는데 오류가 발생했습니다.")
        
        self.player.append({'url': url, 'title': player['title'], 'thumbnail': player['thumbnail'], 'author': player['author']})


        if msg:
            await self.queue_embed(msg, player)
        else:
            await self.queue_embed(ctx, player)

        if not self.playing:
            await self.play(ctx)

    async def queue_embed(self, ctx, data):
        title = data['title'] if type(data['title']) == str else data['title'][0]
        url = data['url'] if type(data['url']) == str else data['url'][0]
        thumbnail = data['thumbnail'] if type(data['thumbnail']) == str else data['thumbnail'][0]
        if type(data['author']) == str:
            author = data['author']
        else:
            if data['author'][0] == None:
                author = "알 수 없음"
            else:
                author = data['author'][0]
        length = len(data['title']) if type(data['title']) == list else 1
        embed = Embed(title=title, url=url)
        embed.set_author(name='예약')
        embed.add_field(name="예약 성공!", value=f'{len(self.player)-self.current-length}번째에 재생됩니다.')
        embed.add_field(name="요청자", value=author, inline=True)
        embed.add_field(name="추가된 재생목록 수", value=f"{length}개", inline=True)
        embed.set_image(url=thumbnail)

        await ctx.edit(embed=embed)
        await ctx.delete(delay=5)

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
                player = await self.download(ctx, self.player[self.current]['url'])
                try:
                    current_subtitles = next((subtitle for subtitle in self.subtitles if subtitle['title'] == player.title), None)
                except:
                    current_subtitles = None
                # 재생 중인 음악 정보 출력
                embedtitle = discord.Embed(title=player.title, url=self.player[self.current]['url'])
                embedtitle.set_author(name="현재 재생중~")
                embedtitle.set_image(url=self.player[self.current]['thumbnail'])
                embedtitle.add_field(name="요청자", value="``" + self.player[self.current]['author'] + "``", inline=True)
                # 다음곡
                if self.current + 1 < len(self.player):
                    embedtitle.add_field(name="다음곡", value=f"[{self.player[self.current + 1]['title']}]({self.player[self.current + 1]['url']})", inline=True)
                else:
                    embedtitle.add_field(name="다음곡", value="``없음``", inline=True)
                

                duration_hour = player.duration // 3600
                duration_min = (player.duration % 3600) // 60
                duration_sec = player.duration % 60
                # duration_hour가 0이면 출력하지 않음
                duration_time = f"{duration_hour}:{duration_min:02d}:{duration_sec:02d}" if duration_hour != 0 else f"{duration_min:02d}:{duration_sec:02d}"

                channel = self.app.get_channel(888048290141179938)
                print_log = f"``{str(datetime.now())}Channel:{str(ctx.guild.name)} | Playing: {str(player.title)} | duration: {duration_time}``"
                await channel.send(print_log)
                print(print_log)
                embedtitle.set_footer(text="0:00 / " + duration_time)
                view = playControlPanel(ctx, self)
                sendmessage = await ctx.send(embed=embedtitle, view=view)
                view.initMsg(sendmessage)

                language_reactions = {
                    'ko': "🇰🇷",
                    'en': "🇺🇸",
                    'ja': "🇯🇵",
                    'zh-CN': "🇨🇳",
                    'zh-TW': "🇹🇼"
                }

                subtitle_change = True
                message = ""
                subtitle_current_lang = self.subtitles_language
                # print(f".{current_subtitles}.")
                # TODO: WARNING: [youtube:tab] YouTube Music is not directly supported. Redirecting to https://www.youtube.com/playlist?list=PLGGsmHNEfAuPa-Erf5spGKAfTUwKBy2Af 
                # WARNING: [youtube:tab] YouTube said: INFO - 1 unavailable video is hidden 
                subtitle = None
                if current_subtitles:
                    for sub in current_subtitles.get('subtitles', []):
                        lang = sub.get('lang')
                        if lang in language_reactions:
                            await sendmessage.add_reaction(language_reactions[lang])
                    subtitle = next((sub for sub in current_subtitles['subtitles'] if sub['lang'] == self.subtitles_language), current_subtitles['subtitles'][0] )

                ctx.voice_client.play(player)
                ctx.voice_client.source.volume = self.volume

                # await asyncio.sleep(5)
                first_time = tt.time() # 코드 걸린 시간을 포함해서 1초를 쉬기 위한 변수
                self.now_time = first_time - 1
                while True: # 음악이 재생중일 때
                    if not ctx.voice_client:
                        break
                    if ctx.voice_client.is_paused(): # 음악이 일시정지 상태일 때
                        await asyncio.sleep(0.1) 
                        continue
                    if not ctx.voice_client.is_playing(): # 음악이 재생중이지 않을 때
                        break
                    if self.pasue_time != 0:
                        self.now_time += self.pasue_time
                        self.pasue_time = 0
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
                    embedtitle.add_field(name="요청자", value="``" + self.player[self.current]['author'] + "``", inline=True)
                    # 다음곡
                    if self.current + 1 < len(self.player):
                        embedtitle.add_field(name="다음곡", value=f"[{self.player[self.current + 1]['title']}]({self.player[self.current + 1]['url']})", inline=True)
                    else:
                        embedtitle.add_field(name="다음곡", value="``없음``", inline=True)
                    # duration_hour가 0이면 출력하지 않음
                    duration_time = f"{duration_hour}:" + f"{duration_min:02d}:" + f"{duration_sec:02d}" if duration_hour != 0 else f"{duration_min:02d}:" + f"{duration_sec:02d}"
                    # time이 1시간 이상이면 시간도 출력
                    time_hour = int(time) // 3600
                    time_min = (int(time) % 3600) // 60
                    time_sec = int(time) % 60
                    time_str = f"{time_hour}:" + f"{time_min:02d}:" + f"{time_sec:02d}" if time_hour != 0 else f"{time_min:02d}:" + f"{time_sec:02d}"
                    embedtitle.set_footer(text=time_str + " / " + duration_time)
                    # 자막 출력
                    if subtitle:
                            
                        message = f"```yaml\n{subtitle['subtitles'][self.subtitles_index]['text']}\n```"

                        if len(subtitle['subtitles']) > self.subtitles_index + 1:
                            message += f"```brainfuck\n{subtitle['subtitles'][self.subtitles_index + 1]['text']}\n```"
                        else:
                            message += "```brainfuck\n End \n ```"
                        embedtitle.add_field(name="자막", value=message[:900], inline=False)
                        if current_subtitles and subtitle_change:
                            subtitle_change = False
                            await sendmessage.edit(embed=embedtitle)
                        else:
                            if time + 1 < subtitle['subtitles'][self.subtitles_index]['time']:
                                await asyncio.sleep(0.5)
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
            
            if self.music_loop == '반복' and self.current + 1 == len(self.player):
                self.current = 0

            elif self.music_loop != "한곡":
                self.current += 1
            try:
                await sendmessage.delete()
            except:
                pass
        await ctx.send("재생목록이 끝났습니다 :)", delete_after=5)
        self.playing = False
        self.reset()

    async def command_play(self, ctx, url):
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
            if ctx.response.is_done():
                await ctx.send_followup(content="재생목록을 발견했습니다. 추가할 방법을 선택해주세요.", view=view)    
            else:
                await ctx.respond("재생목록을 발견했습니다. 추가할 방법을 선택해주세요.", view=view)

        else:
            if "?si=" in url:
                url = url.split("?si=")[0]
            await self.queue(ctx, url)

    async def command_skip(self, ctx):
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if not ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있지 않습니다.")
        ctx.voice_client.stop()
        try:
            await ctx.respond("음악을 건너뛸게요.", delete_after=5)
        except:
            await ctx.send("음악을 건너뛸게요.", delete_after=5)

    async def command_stop(self, ctx):
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            self.reset()
        await ctx.voice_client.disconnect()
        try:
            await ctx.respond("음성 채널에서 퇴장했습니다.", delete_after=5)
        except:
            await ctx.send("음성 채널에서 퇴장했습니다.", delete_after=5)
        await ctx.delete(delay=5)

    async def command_pause(self, ctx):
        self.pasue_time = tt.time()
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if not ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있지 않습니다.")
        ctx.voice_client.pause()
        # await ctx.respond("음악을 일시정지했습니다.", delete_after=5)

    async def command_resume(self, ctx):
        self.pasue_time = tt.time() - self.pasue_time
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있습니다.")
        ctx.voice_client.resume()
        # await ctx.respond("음악을 다시 재생합니다.", delete_after=5)

    async def command_prev(self, ctx):
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if not ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있지 않습니다.")
        if self.current == 0:
            raise CustomError("이전 곡이 없습니다.")
        self.current -= 2
        ctx.voice_client.stop()
        # await ctx.respond("이전 곡을 재생합니다.", delete_after=5)

    async def command_volume(self, ctx, volume):
        volume = int(volume)
        if ctx.voice_client is None:
            raise CustomError("음성 채널에 봇이 없습니다.")
        if not ctx.voice_client.is_playing():
            raise CustomError("음악이 재생되고 있지 않습니다.")
        if volume < 0 or volume > 100:
            raise CustomError("볼륨은 0 ~ 100 사이로 설정해주세요.")
        self.volume = volume / 100
        ctx.voice_client.source.volume = self.volume
        if ctx.response.is_done():
            await ctx.send(f"볼륨을 {volume}%로 조절했습니다.", delete_after=5)
        else:
            await ctx.respond(f"볼륨을 {volume}%로 조절했습니다.", delete_after=5)

    async def command_queue_list(self, ctx):
        if len(self.player) == 0:
            raise CustomError("재생목록이 비어있습니다.")
        
        embeds = []
        embeds.append(Embed(title="재생목록", description=""))
        msg = ""
        for i in range(len(self.player)):
            temp = f"{i+1}. {self.player[i]['title']}"
            if i == self.current:
                temp += "`현재 재생중`\n"
            else:
                temp += "\n"
            if len(msg + temp) > 900:
                embeds[-1].description = msg
                msg = ""
                embeds.append(Embed(title="재생목록", description=""))
                msg += temp
            else:
                msg += temp
        embeds[-1].description = msg
        # 닫기 버튼 추가
        async def close_callback(interaction):
            await interaction.message.delete()
        
        view = discord.ui.View()
        close_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="닫기", custom_id="close", row=0)
        close_button.callback = close_callback
        view.add_item(close_button)
        

        await ctx.respond(embeds=embeds, view=view)

