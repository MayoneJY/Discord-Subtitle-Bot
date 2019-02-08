import asyncio
import discord
import threading
import sys, os
import youtube_dl
import ffmpeg
import time as t
import urllib.request
import json
from discord.ext import commands

defultvolum = 0.2
defultvideoSub = "any"
channel = discord.Object(id='537842350882291734')
token = "NDE1NDc1NTEzMzU2NzE0MDE0.DzHy7Q.ADQiLT0ny2DLwGQ9Q_bQU3W5Wg0"
beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
def ResetBot():
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    print("재시작 중...")
    os.execvp(executable, args)

queues={}
musiclist=[]
players={}
volumes={}
imgurls={}
servervideosubs={}
def check_queue(id):
    if queues[id]!=[]:
        player = queues[id].pop(0)
        players[id] = player
        del musiclist[0]
        player.volume = volumes[id]
        player.start()

def main():
    app = discord.Client()

    @app.event
    async def on_ready():
        print("다음으로 로그인합니다 : ")
        print(app.user.name)
        print(app.user.id)
        print("==========================")
        await app.send_message(channel, "``음악재생 준비 완료``")
        #await app.change_presence(game=discord.Game(name="!음악 테스트",type=1))

    @app.event
    async def on_message(message):
        global defultvolum
        server = message.server
        try: 
            type(volumes[server.id])
            type(servervideosubs[server.id])
        except KeyError:
            volumes[server.id] = defultvolum
            servervideosubs[server.id] = defultvideoSub

        if message.author.bot:
            return None
        if message.content == "!테스트":
            print(players[server.id].is_live)
        if message.content.startswith("!들어와"):
            channel = message.author.voice.voice_channel
            voice_client = app.voice_client_in(server)
            print("들어와")
            print(voice_client)
            print("들어와")
            if voice_client== None:
                await app.send_message(message.channel, '들어왔습니다') # 호오.... 나를 부르는건가? 네녀석.. 각오는 되있겠지?
                await app.join_voice_channel(channel)
            else:
                await app.send_message(message.channel, '봇이 이미 들어와있습니다.') # 응 이미 들어와있어 응쓰게싸

        if message.content.startswith("!나가"):
                voice_client = app.voice_client_in(server)
                print("나가")
                print(voice_client)
                print("나가")
                if voice_client == None:
                    await app.send_message(message.channel,'봇이 음성채널에 접속하지 않았습니다.') # 원래나가있었음 바보녀석 니녀석의 죄는 "어리석음" 이라는 .것.이.다.
                    pass
                else:
                    await app.send_message(message.channel, '나갑니다') # 나가드림
                    await voice_client.disconnect()
        if message.content == "!자막위주":
            servervideosubs[server.id] = "closedCaption"
            #embed = discord.Embed(
            #    title='음악 정보',
            #    description="음악 서칭을 자막위주로 변경되었습니다.",
            #    colour=discord.Colour.blue()
            #    )
            #await app.send_message(message.channel, embed=embed)

        elif message.content == "!자막위주안함":
            servervideosubs[server.id] = "any"
            #embed = discord.Embed(
            #    title='음악 정보',
            #    description="음악 서칭을 정확도 위주로 변경되었습니다.",
            #    colour=discord.Colour.blue()
            #    )
            #await app.send_message(message.channel, embed=embed)

        elif message.content.startswith("!자막"):
            voice_client = app.voice_client_in(server)
            msg1 = message.content.split(" ")
            print(msg1[1].startswith("http"))
            if msg1[1].startswith("http"):
                url = msg1[1]
                urlcode = message.content.split("v=")
                data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?q="+ urllib.parse.quote(urlcode[1]) +"&videoCaption=" + servervideosubs[server.id] +"&type=video&part=snippet&key=AIzaSyApEAt-uS8udiAR18kNxl6VVoCSHspsF2o&maxResults=1").read()
                output = json.loads(data)
            else:
                Text = ""
                for i in range(1, len(msg1)):
                    Text = Text + " " + msg1[i]
                data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?q="+ urllib.parse.quote(Text) +"&videoCaption=" + servervideosubs[server.id] +"&type=video&part=snippet&key=AIzaSyApEAt-uS8udiAR18kNxl6VVoCSHspsF2o&maxResults=1").read()
                output = json.loads(data)
                ytlink = output['items'][0]['id']['videoId']
                url = "https://www.youtube.com/watch?v=" + ytlink
            try:
                imgurls[server.id] = output['items'][0]['snippet']['thumbnails']['high']['url']
            except IndexError:
                imgurls[server.id] = ""
                print("링크가 유효하지않습니다.")
            try: 
                player = await voice_client.create_ytdl_player(url, after=lambda: check_queue(server.id), before_options=beforeArgs)
            except AttributeError:
                channel = message.author.voice.voice_channel
                await app.join_voice_channel(channel)
                voice_client = app.voice_client_in(server)
                player = await voice_client.create_ytdl_player(url, after=lambda: check_queue(server.id), before_options=beforeArgs)
            players[server.id] = player
            #await app.send_message(message.channel, "``음악재생``")

            player.volume = volumes[server.id]

            player.start()
            t.sleep(0.9)
            await app.send_message(message.channel, "``재생중 : "+ player.title +"``")

        if message.content == "!스톱":
            try:
                type(players[server.id])
                await app.send_message(message.channel, "```종료!```")
                players[server.id].stop()
                del(players[server.id])
            except KeyError:
                await app.send_message(message.channel, "`음악이 재생중이 아닙니다.`")

        if message.content == "!볼륨":
            await app.send_message(message.channel, "`볼륨 : " + str(int(volumes[server.id]*100)) + "%`")
        elif message.content.startswith("!볼륨"):
            voice_client = app.voice_client_in(server)
            msg1 = message.content.split(" ")
            try:
                vol = float(msg1[1]) / 100
            except IndexError:
                await app.send_message(message.channel, "`!볼륨 크기\n이런 형태로 입력해주세요\n크기 : 0~100`")
            try:
                type(volumes[server.id])
                volumes[server.id] = vol
                await app.send_message(message.channel, "`볼륨 : " + str(int(volumes[server.id]*100)) + "%`")
                players[server.id].volume = vol
            except KeyError:
                await app.send_message(message.channel, "`음악이 재생중이 아닙니다.`")

#     !음악 https://www.youtube.com/watch?v=55AalrbALAk
        if message.content.startswith('!예약'):
            msg1 = message.content.split(" ")
            url = msg1[1]
            server = message.server
            voice_client = app.voice_client_in(server)
            player = await voice_client.create_ytdl_player(url, after=lambda: (server.id), before_options=beforeArgs)

            if server.id in queues:
                queues[server.id].append(player)
                print('if 1 '+ str(queues[server.id])) #queues배열 확인
            else:
                queues[server.id] = [player]
                print('else 1' + str(queues[server.id]))#queues배열 확인
            await app.send_message(message.channel,'예약 완료\n')
            musiclist.append(url) #대기목록 링크

        if message.content.startswith('!대기목록'):

            server = message.server
            msg1 = message.content.split(" ")
            mList = msg1[1]
            num = 0
            bSize = len(musiclist) # 배열 사이즈 크기구함

            if mList =='보기':
                embed = discord.Embed(
                    title='대기중인 곡 들',
                    description='대기중.....',
                    colour=discord.Colour.blue()
                )
                for i in musiclist:
                    print('예약리스트 : ' + i)
                    embed.add_field(name='대기중인 곡', value=i, inline=False)
                await app.send_message(message.channel, embed=embed)

            if mList =='취소':
                while num<bSize:
                    del musiclist[0]
                    num = num+1

                del queues[server.id]
                await app.send_message(message.channel,'예약중인 음악 모두 취소 완료')

        if message.content == "!정보":
            try:
                type(players[server.id])
                embed = discord.Embed(
                    title='음악 정보',
                    description="``"+players[server.id].title+"`` 재생 중\n"+players[server.id].url+"\n"+str(int(players[server.id].duration/60))+"분 "+str(players[server.id].duration - int(players[server.id].duration/60)*60)+"초",
                    colour=discord.Colour.blue()
                )
                embed.set_image(url = imgurls[server.id])
                await app.send_message(message.channel, embed=embed)
            except KeyError:
                await app.send_message(message.channel, "`음악이 재생중이 아닙니다.`")
    app.run(token)
    ResetBot()


if __name__ == '__main__':
    main()
