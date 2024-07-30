from discord.ext import commands
from discord.commands import slash_command
from utils.error import CustomError
from utils.music import Music

guilds = {}


def setup(app):
    app.add_cog(Core(app))



guild_ids = ["1016514629603700766","537629446878920733","888048290141179934","1052491958859345935"]

class Core(commands.Cog, name="뮤직봇"):

    def __init__(self, app):
        self.app = app
        self.loop = app.loop

    @slash_command(name="join", description="음성 채널에 봇을 초대합니다.", guild_ids=guild_ids)
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.respond("음성 채널에 먼저 들어가주세요.", delete_after=5)
            return
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        await ctx.author.voice.channel.connect()
        await ctx.respond("음성 채널에 입장했습니다.", delete_after=5)

    @slash_command(name="stop", description="노래 정지 후 음성 채널에서 봇을 퇴장시킵니다.")
    async def stop(self, ctx):
        if guilds.get(ctx.guild.id):
            guilds[ctx.guild.id].command_stop(ctx)
        else:
            raise CustomError("음악이 재생되고 있지 않습니다.")

    @slash_command(name="play", description="음악을 재생합니다.", guild_ids=guild_ids)
    async def play(self, ctx, url: str):
        if not ctx.response.is_done():
            await ctx.defer()
        # await ctx.respond("로딩중...", delete_after=2)
        if not guilds.get(ctx.guild.id):
            guilds[ctx.guild.id] = Music(self.loop)

        await guilds[ctx.guild.id].command_play(ctx, url)


    @slash_command(name="skip", description="음악을 건너뜁니다.", guild_ids=guild_ids)
    async def skip(self, ctx):
        if not guilds.get(ctx.guild.id):
            raise CustomError("음악이 재생되고 있지 않습니다.")
        await guilds[ctx.guild.id].command_skip(ctx)
        
    
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
            raise CustomError("음성채널에 연결되지 않았습니다.")  # 출력
    # @commands.Cog.listener()
    # async def check_guilds(self, ctx):
    #     if not guilds.get(ctx.guild.id):
    #         guilds[ctx.guild.id] = Music()


    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        
        if reaction.message.author.bot:
            if reaction.emoji == "🇰🇷":
                guilds[reaction.message.guild.id].subtitles_language = "ko"
            elif reaction.emoji == "🇺🇸":
                guilds[reaction.message.guild.id].subtitles_language = "en"
            elif reaction.emoji == "🇯🇵":
                guilds[reaction.message.guild.id].subtitles_language = "ja"
            elif reaction.emoji == "🇨🇳":
                guilds[reaction.message.guild.id].subtitles_language = "zh-CN"
            elif reaction.emoji == "🇹🇼":
                guilds[reaction.message.guild.id].subtitles_language = "zh-TW"
            await reaction.message.remove_reaction(reaction.emoji, user)
        return
        