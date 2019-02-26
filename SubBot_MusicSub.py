import asyncio
import discord
import threading
import math
from bs4 import BeautifulSoup
import urllib.request
import time as t
import sys, os
import json
import youtube_dl
import ffmpeg
from discord.ext import commands
# 제작자 : 남정연 (mayone6063@naver.com)
# 수정자 : 
# 깃허브 : https://github.com/akso6063/Discord-Subtitle-Bot

# 제가 제작한 코드를 사용하시는건 괜찮지만 제작자이름을 지우지 말아주세요 :(
# 수정은 자유입니다. 제작자 이름만 냅둬주세요.

# 뮤직 봇과 함께 사용하는 자막 봇,
# 유튜브에 있는 자막을 가져와 싱크에 맞춰 디스코드 채팅에 올려집니다..


# 주의할 점
# 한 서버에서 사용하는 것을 권장합니다. 여러서버를 동시에 사용하면 코드가 꼬이게 코딩되어 있습니다.
# 노래가 재생 중에 !자막 커맨드를 사용하지 마세요! 딜레이 또는 자막이 겹칩니다.
# EX) !자막 https://www.youtube.com/watch?v=oIa3BFBHJFI
# EX) !자막 태보
# v= 뒤에 코드가 꼭 있어야함.
# 템포가 빠른 자막은 딜레이가 심해집니다..

# 봇이 입력될 채팅 채널 아이디와 토큰을 적어주세요.
channel = discord.Object(id='##################')
token = "###########################################################"

# 자막이 시작 될 때 싱크가 맞지않다면 수정해주세요 기본 값: 6.5초
# 영상이 짧거나 길때 약간씩 어긋납니다. 그 점 양해해주세요
# 사용안함
#SetFirstSleep = 6.5

# 영상 길이가 짧을 때 영상받아오는 속도가 빠르므로 그 만큼 딜레이를 줘야하기 때문에
# 사용되는 변수  영상 길이 기본 값: 140초
# 사용안함
#SetVideoLength = 140

# 자막 언어 한국어: ko  日本語: ja  English: en
SetLanguege = "ko"

# 기본볼륨 0.2(20%)
defaultvolum = 0.2

# 자막이 있는 영상만 찾으려면 closedCaption을 자막이 없는영상도 포함하려면 any를 입력해주세요
defaultvideoSub = "any"

# 봇 사용 예시입니다.
# !자막 https://www.youtube.com/watch?v=cvxm8GJJHqQ
# !자막 https://www.youtube.com/watch?v=J1AdPY73qxo
# !자막 https://www.youtube.com/watch?v=oIa3BFBHJFI
# !자막 https://www.youtube.com/watch?v=rDG9I9nx0QU
# !자막 https://www.youtube.com/watch?v=55AalrbALAk
# !자막 180도
# !자막 태보

cmdlist = '```!커맨드, !명령어, !도움말, !자막, !언어변경, !한국어, !일본어, !영어, !볼륨, !스톱, !자막위주, !자막위주안함```	'

cmdembed = discord.Embed(
	title='커맨드 목록',
	description="\n",
	colour=discord.Colour.blue()
)
cmdembed.add_field(name='!커맨드, !명령어, !도움말', value="여러 커맨드의 목록과 설명을 알려주는 커맨드.\n", inline=False)
cmdembed.add_field(name='!자막', value="``!자막 <link>``\n``!자막 <title>``\n유튜브를 틀어주는 커맨드.\n", inline=False)
cmdembed.add_field(name='!스톱', value="영상을 그만트는 커맨드.", inline=False)
cmdembed.add_field(name='!언어변경', value="``!언어변경 <lang_code>``\n자막 언어를 변경해주는 커맨드.\n!언어 <link>로 그 영상의 자막 lang_code를 얻을 수 있음.\n", inline=False)
cmdembed.add_field(name='!한국어, !일본어, !영어', value="자막의 언어를 각 언어로 변경해주는 커맨드.\n", inline=False)
cmdembed.add_field(name='!볼륨', value="``!볼륨``\n현재 볼륨크기를 알려주는 커맨드.\n``!볼륨 <number>``\n볼륨을 <number>으로 바꿔주는 커맨드. 0~100까지 사용가능하다.\n", inline=False)
cmdembed.add_field(name='!자막위주', value="자막영상위주로 서칭하는 커맨드.\n", inline=False)
cmdembed.add_field(name='!자막위주안함', value="정확도위주로 서칭하는 커맨드.\n", inline=False)
cmdembed.add_field(name='!정보', value="마지막으로 추가된 영상의 정보를 알려주는 커맨드.\n", inline=False)




def ResetBot():
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    print("재시작 중...")
    os.execvp(executable, args)

servervideosubs={}
SubTime = []
SubText = []
msstops={}
SubNum = 0
NowTime = 0
lankr = "언어 : 한국어\n言語 : 韓国語\nLanguege : korean"
lanen = "언어 : 영어\n言語 : 英語\nLanguege : English"
lanja = "언어 : 일본어\n言語 : 日本語\nLanguege : japanese"


def main():
	global SubTime
	global SubText
	global SubNum
	global NowTime
	app = discord.Client()

    
	SubTime = []
	SubText = []
	SubNum = 0
	NowTime = 0
	
	async def BotSub(server):
		global SubNum
		global NowTime
		
		try:
			if SubTime[SubNum] == 9999:
				await app.send_message(channel, "```자막이 없습니다!```")
		except IndexError:
			await app.send_message(channel, "```자막기능을 사용하지 않습니다.```")

		SleepTimeFirst = t.time()
		first1 = True
		
		while(True):
			if msstops[server.id] == True or SubNum == len(SubText) or SubTime[SubNum] == 9999:
				SubNum = 0
				SubText.clear()
				SubTime.clear()
				NowTime = 0
				msstops[server.id] = False
				await app.send_message(channel, "``노래방재생 준비 완료!``")
				break
			sleeptime = 1
			if NowTime >= SubTime[SubNum]:
				if NowTime >= SubTime[SubNum+1]:
					if NowTime >= SubTime[SubNum+2]:
						if NowTime >= SubTime[SubNum+3]:
							await app.send_message(channel, "```"+SubText[SubNum]+ "```" + "```" + SubText[SubNum+1] + "```" + "```" + SubText[SubNum+2] + "```" + "```" + SubText[SubNum+3]+"```")
							SubNum += 4
						else:
							await app.send_message(channel, "```"+SubText[SubNum]+ "```" + "```" + SubText[SubNum+1] + "```" + "```" + SubText[SubNum+2] + "```")
							SubNum += 3
					else:
						await app.send_message(channel, "```"+SubText[SubNum]+ "```" + "```" + SubText[SubNum+1] + "```")
						SubNum += 2
				else:
					await app.send_message(channel, "```"+SubText[SubNum]+"```")
					SubNum += 1
			
			SleepTimeSecond = t.time()
			sleepp = SleepTimeSecond - SleepTimeFirst
			#NowTimeDelay = False
			if(sleepp > 1):
				if(sleepp > 2):
					sleeptime = int(sleepp) + 1 - sleepp
					printsend = ""
					for i in range(int(sleepp) - 1):
						#NowTimeDelay = True
						NowTime += 1
						if NowTime >= SubTime[SubNum-1]:
							#print("진입" + SubText[SubNum])
							printsend += "```"+SubText[SubNum]+"```"
							SubNum += 1
					await app.send_message(channel, printsend)
				else:
					sleeptime -= sleepp - 1
			else:
				if(first1 == True):
					sleeptime = 0
					first1 = False
				else:
					sleeptime += 1 - sleepp
			print(str(NowTime)+"   "+str(SubTime[SubNum])+"   "+str(SleepTimeFirst)+"   "+str(SleepTimeSecond)+"   "+str(sleeptime))
			t.sleep(sleeptime)
			SleepTimeFirst = SleepTimeSecond + sleeptime - 1
			#if(NowTimeDelay == True):
			#	NowTimeDelay = False
			#else:
			#	NowTime += 1
			NowTime += 1


	@app.event
	async def on_ready():
		print("다음으로 로그인합니다 : ")
		print(app.user.name)
		print(app.user.id)
		print("==========================")
		await app.send_message(channel, "``자막 준비 완료!``")
		await app.change_presence(game=discord.Game(name="!도움말       (Made by Mayone)",type=1))
		
	@app.event
	async def on_message(message):
		global SetLanguege
		global defaultvolum
		server = message.server
		try: 
			type(servervideosubs[server.id])
			type(msstops[server.id])
		except KeyError:
			servervideosubs[server.id] = defaultvideoSub
			msstops[server.id] = False

		if message.author.bot:
			if message.content.startswith("``재생중 : "):
				await BotSub(server)
			else:
				return None
			#return None
		if message.content == ("!커맨드") or message.content == ("!도움말") or message.content == ("!명령어") :
			
			await app.send_message(message.channel,embed=cmdembed)

		
		if message.content == "!자막위주":
			servervideosubs[server.id] = "closedCaption"
			embed = discord.Embed(
				title='음악 정보',
				description="음악 서칭을 자막위주로 변경되었습니다.",
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)

		elif message.content == "!자막위주안함":
			servervideosubs[server.id] = "any"
			embed = discord.Embed(
				title='음악 정보',
				description="음악 서칭을 정확도 위주로 변경되었습니다.",
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)


		elif message.content.startswith("!자막"):
			#global SetFirstSleep
			#global SetVideoLength
			#FirstSleep = SetFirstSleep
			Languege = SetLanguege
			#VideoLength = SetVideoLength
			
			mecont = message.content.split(" ")
			imglink = ""
			if mecont[1].startswith("http"):

				mecont = message.content
				mecont2 = mecont.split("v=")
				ytlink = mecont2[1]
				ytlink = ytlink[0:11]
				url = "https://www.youtube.com/api/timedtext?lang="+ Languege +"&v=" + ytlink
			else:
				Text = ""
				for i in range(1, len(mecont)):
					Text = Text + " " + mecont[i]
				
				data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?q="+ urllib.parse.quote(Text) + "&videoCaption=" + servervideosubs[server.id] +"&type=video&part=snippet&key=AIzaSyApEAt-uS8udiAR18kNxl6VVoCSHspsF2o&maxResults=1").read()
				output = json.loads(data)
				ytlink = output['items'][0]['id']['videoId']
				imglink = output['items'][0]['snippet']['thumbnails']['high']['url']
				url = "https://www.youtube.com/api/timedtext?lang="+ Languege +"&v=" + ytlink


			request = urllib.request.urlopen(url)
			xml = request.read()
			soup = BeautifulSoup(xml,"html.parser")
			appendnum = 0
			for result in soup.find_all("text"):
				appendtime = math.floor(float(result['start']))
				if appendnum != 0:
					if appendtime - SubTime[appendnum-1] > 10:
						for i in range(math.floor(((appendtime - SubTime[appendnum-1]) / 10))-1):
							SubTime.append(SubTime[appendnum-1]+10)
							SubText.append(".")
							appendnum += 1
				else: 
					if appendtime > 10:
						for i in range(math.floor((appendtime / 10))-1):
							SubTime.append((10 * (i + 1)))
							SubText.append(".")
							appendnum += 1

				SubTime.append(appendtime)
				if result.string == " ":
					SubText.append(".")
				else:
					SubText.append(result.string)
				appendnum += 1
			urllistresult = "노래재생 시작전에 !언어변경 <lang_code> (으)로 자막언어를 변경할 수 있습니다.\n/ "
			urllist = "https://www.youtube.com/api/timedtext?type=list&v=" + ytlink
			request = urllib.request.urlopen(urllist)
			xml = request.read()
			soup = BeautifulSoup(xml,"html.parser")
			for result in soup.find_all("track"):
				urllistresult += result['lang_original'] + "[" + result['lang_code'] + "]" +  " / "
			if SetLanguege == "ko":
				infolantp = lankr
			elif SetLanguege == "en":
				infolantp = lanen
			elif SetLanguege == "ja":
				infolantp = lanja
			else:
				infolantp = "언어코드(Lang_Code) : " + SetLanguege
			
			#print(urllistresult)
			try:
				embed = discord.Embed(
					title='자막 설정',
					description=infolantp,
					colour=discord.Colour.blue()
				)
				
				embed.add_field(name='유튜브 링크', value="https://www.youtube.com/watch?v="+ytlink, inline=False)
				if urllistresult == "노래재생 시작전에 !언어변경 <lang_code> (으)로 자막언어를 변경할 수 있습니다.\n/ ":
					urllistresult += "자막 없음."
				embed.add_field(name='자막 목록  lang_original[lang_code]', value=urllistresult, inline=False)
			
			except discord.errors.HTTPException:
				embed = discord.Embed(
					title='자막 설정',
					description=infolantp,
					colour=discord.Colour.blue()
				)
				
				embed.add_field(name='유튜브 링크', value="https://www.youtube.com/watch?v="+ytlink, inline=False)
			
				urllistresult = "자막 수가 너무 많아 모두 입력하지 못합니다."
				embed.add_field(name='자막 목록', value=urllistresult, inline=False)
			if imglink != "":
				embed.set_image(url = imglink)
			await app.send_message(message.channel, embed=embed)
			#if SubTime[appendnum-1] < VideoLength:
			#	FirstSleep += 2.5
			SubTime.append(9999)
			SubTime.append(9999)
			SubTime.append(9999)
			#t.sleep(FirstSleep)
			#await BotSub()


		if message.content.startswith("!스톱"):
			#ResetBot()
			msstops[server.id] = True

		if message.content == "!한국어" or message.content == "!korean" or message.content == "!韓国語":
			SetLanguege = "ko"
			embed = discord.Embed(
				title='음악 정보',
				description=lankr,
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)
		if message.content == "!English" or message.content == "!영어" or message.content == "!英語":
			SetLanguege = "en"
			embed = discord.Embed(
				title='음악 정보',
				description=lanen,
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)
		if message.content == "!日本語" or message.content == "!일본어" or message.content == "!japanese":
			SetLanguege = "ja"
			embed = discord.Embed(
				title='음악 정보',
				description=lanja,
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)
		if message.content.startswith("!언어변경"):
			langtext = message.content.split(" ")
			SetLanguege = langtext[1]
			embed = discord.Embed(
				title='음악 정보',
				description=SetLanguege + "(으)로 변경되었습니다.",
				colour=discord.Colour.blue()
			)
			await app.send_message(message.channel, embed=embed)
		if message.content.startswith("!언어"):
			url = message.content.split("v=")
			url = url[0:11]
			urllist = "https://www.youtube.com/api/timedtext?type=list&v=" + url[1]
			request = urllib.request.urlopen(urllist)
			xml = request.read()
			soup = BeautifulSoup(xml,"html.parser")
			urllistresult = ""
			cnt = 0
			for result in soup.find_all("track"):
				urllistresult += result['lang_original'] + "[" + result['lang_code'] + "]" +  " / "
				cnt += 1
				if cnt == 20:
					await app.send_message(message.channel, "``"+urllistresult+"``")
					urllistresult = ""
					cnt = 0
			
			await app.send_message(message.channel, "``"+urllistresult+"``")

	app.run(token)
	ResetBot()
    

if __name__ == '__main__':
    main()
