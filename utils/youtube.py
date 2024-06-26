
from yt_dlp import YoutubeDL

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
    async def from_title(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl2.extract_info(f"ytsearch5:{url}", download=stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        if data == []:
            return 1
        else:
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

            return data2
    
    
    @classmethod
    async def from_list(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl2.extract_info(url, download=stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
        if data == []:
            return 1
        else:
            data2 = []
            data2.append(data[0]['id'])
            data2.append(data[0]['title'])
            try:
                for i in range(1, len(data[0])):
                    data2.append(data[i]['id'])
                    data2.append(data[i]['title'])
            except:
                pass

            return data2