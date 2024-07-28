from requests import Session
import re
import time as tt

class Subtitle:
    async def import_subtitles(info):
        clean = '<.*?>'
        subtitles_temp = {'title': info.get('title'), 'subtitles': []}
        has_subtitles = False
        f_t = tt.time()
        with Session() as session:
            for k, subtitles_list in info.get('subtitles', {}).items():
                if '-' in k and len(k.split('-')[1]) > 2:
                    continue
                if k == 'live_chat':
                    continue
                # 한국어 영어 일본어 중국어만
                if k not in ['ko', 'en', 'ja', 'zh-CN', 'zh-TW']:
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
                        if len(tempTimes) == 0:
                            tempTimes.append(time)
                        elif time >= tempTimes[-1]:
                            tempTimes.append(time)
                        else:
                            break
                        chk = True
                        # if len(tempTimes) == 0 or time - tempTimes[-1] > 1:
                        #     tempTimes.append(time)
                        #     chk = True
                        # else:
                        #     chk = False

                    else:
                        #subtitle
                        if chk:
                            tempSubtiles.append(line.strip())
                            chk = False
                        else:
                            tempSubtiles[-1] += "\n" + line.strip()
                print("before", len(tempSubtiles), len(tempTimes))
                i = 1
                while i < len(tempSubtiles): 

                    if tempSubtiles[i] == tempSubtiles[i - 1]:
                        del tempSubtiles[i]
                        del tempTimes[i]
                        i -= 1

                    elif tempTimes[i] - tempTimes[i - 1] < 1:
                        tempSubtiles[i - 1] += "\n" + tempSubtiles[i]
                        del tempSubtiles[i]
                        del tempTimes[i]
                        i -= 1
                    i += 1

                tempSubtiles.insert(0, " ")
                tempSubtiles.append(" ")
                tempSubtiles.append(" ")
                tempTimes.append(99999)
                tempTimes.append(99999)
                tempTimes.append(99999)
                print("after", len(tempSubtiles), len(tempTimes))
                # print(tempSubtiles, tempTimes)
                for i in range(len(tempTimes)):
                    subtitles_lang_temp.get('subtitles').append({'text': tempSubtiles[i], 'time': tempTimes[i]})
                subtitles_temp.get('subtitles').append(subtitles_lang_temp)
        print("총 " + str(tt.time() - f_t) + "초 걸림")
        if has_subtitles:
            return subtitles_temp
        else:
            return None