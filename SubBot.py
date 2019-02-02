import asyncio
import discord
import threading
import math
from bs4 import BeautifulSoup
import urllib.request
import time as t
import sys, os

# 제작자 : 남정연 (mayone6063@naver.com)
# 수정자 : 
# 깃허브 : https://github.com/akso6063/Discord-Subtitle-Bot

# 제가 제작한 코드를 사용하시는건 괜찮지만 제작자이름을 지우지 말아주세요 :(
# 수정은 자유입니다. 제작자 이름만 냅둬주세요.

# 뮤직 봇과 함께 사용하는 자막 봇,
# 유튜브에 있는 자막을 가져와 싱크에 맞춰 디스코드 채팅에 올려집니다..


# 주의할 점
# 한 서버에서 사용하는 것을 권장합니다. 여러서버를 동시에 사용하면 코드가 꼬이게 코딩되어 있습니다.
# 노래가 재생 중에 !노래방재생 커맨드를 사용하지 마세요! 딜레이 또는 자막이 겹칩니다.
# 노래방재생을 이용할 때 꼭 링크를 달아주세요! 안그럼 작동을 안합니다!.
# EX) !노래방재생 https://www.youtube.com/watch?v=oIa3BFBHJFI
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

# 기본 자막 언어 한국어: ko  日本語: ja  English: en
SetLanguege = "ko"

# 봇 사용 예시입니다.
# !노래방재생 https://www.youtube.com/watch?v=cvxm8GJJHqQ
# !노래방재생 https://www.youtube.com/watch?v=J1AdPY73qxo
# !노래방재생 https://www.youtube.com/watch?v=oIa3BFBHJFI
# !노래방재생 https://www.youtube.com/watch?v=rDG9I9nx0QU
# !노래방재생 https://www.youtube.com/watch?v=55AalrbALAk


def ResetBot():
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    print("재시작 중...")
    os.execvp(executable, args)

SubTime = []
SubText = []
SubNum = 0
NowTime = 0

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

	async def BotSub():
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
			sleeptime = 1
			if NowTime == SubTime[SubNum]:
				if NowTime == SubTime[SubNum+1]:
					if NowTime == SubTime[SubNum+2]:
						if NowTime == SubTime[SubNum+3]:
							await app.send_message(channel, "```"+SubText[SubNum]+ "\n" + SubText[SubNum+1] + "\n" + SubText[SubNum+2] + "\n" + SubText[SubNum+3]+"```")
							SubNum += 4
						else:
							await app.send_message(channel, "```"+SubText[SubNum] + "\n" + SubText[SubNum+1] + "\n" + SubText[SubNum+2]+"```")
							SubNum += 3
					else:
						await app.send_message(channel, "```"+SubText[SubNum] + "\n" + SubText[SubNum+1]+"```")
						SubNum += 2
				else:
					await app.send_message(channel, "```"+SubText[SubNum]+"```")
					SubNum += 1
				if SubNum == len(SubText):
					SubNum = 0
					SubText.clear()
					SubTime.clear()
					NowTime = 0
					await app.send_message(channel, "``노래방재생 준비 완료!``")
					break
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
							printsend += SubText[SubNum] + "\n" 
							SubNum += 1
					await app.send_message(channel, "```"+printsend+"```")
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
		await app.send_message(channel, "``노래방재생 준비 완료!``")
		await app.change_presence(game=discord.Game(name="!노래방재생 사용가능",type=1))
		
	@app.event
	async def on_message(message):
		global SetLanguege
		if message.author.bot:
			if message.content.startswith("Now playing in"):
				await BotSub()
			else:
				return None
		
		if message.content.startswith("!노래방재생"):
			#global SetFirstSleep
			#global SetVideoLength
			#FirstSleep = SetFirstSleep
			Languege = SetLanguege
			#VideoLength = SetVideoLength
			mecont = message.content
			mecont2 = mecont.split("v=")
			url = "https://www.youtube.com/api/timedtext?lang="+ Languege +"&v=" + mecont2[1]
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
			#if SubTime[appendnum-1] < VideoLength:
			#	FirstSleep += 2.5
			SubTime.append(9999)
			SubTime.append(9999)
			SubTime.append(9999)
			#t.sleep(FirstSleep)
			#await BotSub()
		if message.content.startswith("!스킵"):
			ResetBot()
		if message.content == "!한국어" or message.content == "!korean" or message.content == "!韓国語":
			SetLanguege = "ko"
			await app.send_message(channel, "``언어 : 한국어\n言語 : 韓国語\nLanguege : korean``")
		if message.content == "!English" or message.content == "!영어" or message.content == "!英語":
			SetLanguege = "en"
			await app.send_message(channel, "``언어 : 영어\n言語 : 英語\nLanguege : English``")
		if message.content == "!日本語" or message.content == "!일본어" or message.content == "!japanese":
			SetLanguege = "ja"
			await app.send_message(channel, "``언어 : 일본어\n言語 : 日本語\nLanguege : japanese``")
	app.run(token)
	ResetBot()
    

if __name__ == '__main__':
    main()
