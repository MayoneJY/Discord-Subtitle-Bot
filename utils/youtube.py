
from yt_dlp import YoutubeDL
import discord
import asyncio

SubtitleLanguages = ["ko", "en", "ja"]
ytdl_format_options = {
    # 'writesubtitles': True,
    # 'subtitleslangs': SubtitleLanguages,
    # 'writethumbnail' : True,
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'no_overwrites': True,
}
ydl_opts = {
    'default_search': 'ytsearch',  # YouTube 검색 모드
    'quiet': True,                # 출력 최소화
    'extract_flat': True,         # 세부 정보 생략 (URL 목록만 추출)
    'noplaylist': True,           # 플레이리스트 제외
}

ffmpeg_options = {
    'options': '-vn'
}

ydl = YoutubeDL(ytdl_format_options)
ydl2 = YoutubeDL(ydl_opts)




class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    def from_url(cls, url, *, stream=False):
        data = ydl.extract_info(url, download=not stream)
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ydl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    
    @classmethod
    async def from_title(cls, url, author, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl2.extract_info(f"ytsearch5:{url}", download=stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        if data == []:
            return 1
        else:
            data2 = {'url': [], 'title': [], 'thumbnail': [], 'author': []}
            data2['url'].append(data[0]['url'])
            data2['title'].append(data[0]['title'])
            data2['thumbnail'].append(data[0]['thumbnails'][-1]['url'])
            data2['author'].append(author)
            try:
                if len(data[0]) >= 5:
                    for i in range(1, 5):
                        data2['url'].append(data[i]['url'])
                        data2['title'].append(data[i]['title'])
                        data2['thumbnail'].append(data[i]['thumbnails'][-1]['url'])
                        data2['author'].append(author)
                else:
                    for i in range(1, len(data[0])):
                        data2['url'].append(data[i]['url'])
                        data2['title'].append(data[i]['title'])
                        data2['thumbnail'].append(data[i]['thumbnails'][-1]['url'])
                        data2['author'].append(author)
            except:
                pass

            return data2
        
    @classmethod
    async def from_title_solo(cls, url, author, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl2.extract_info(f"ytsearch1:{url}", download=stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        if data == []:
            return 1
        else:
            data2 = {}
            data2['url'] = data[0]['url']
            data2['title'] = data[0]['title']
            data2['thumbnail'] = data[0]['thumbnails'][-1]['url']
            data2['author'] = author

            return data2
    
    
    @classmethod
    async def from_list(cls, url, author, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl2.extract_info(url, download=stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        if data == []:
            return 1
        else:
            data2 = {'url': [], 'title': [], 'thumbnail': [], 'author': []}
            data2['url'].append(data[0]['url'])
            data2['title'].append(data[0]['title'])
            data2['thumbnail'].append(data[0]['thumbnails'][-1]['url'])
            data2['author'].append(author)
            
            try:
                for i in range(1, len(data)):
                    data2['url'].append(data[i]['url'])
                    data2['title'].append(data[i]['title'])
                    data2['thumbnail'].append(data[i]['thumbnails'][-1]['url'])
                    data2['author'].append(author)
            except:
                pass
            
            print(data2)
            return data2