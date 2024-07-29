from discord.ui import Select, View, Button
from discord.ui.button import ButtonStyle
from discord import Embed

class ListView(View):
    def __init__(self, ctx, music, url):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.music = music
        self.url = url
        
        self.button1 = Button(style=ButtonStyle.primary, label="처음 곡부터 추가", custom_id="1")
        self.button2 = Button(style=ButtonStyle.primary, label="현재 곡부터 추가", custom_id="2")
        self.button3 = Button(style=ButtonStyle.primary, label="한 곡만 추가", custom_id="3")

        self.button1.callback = self.first
        self.button2.callback = self.current
        self.button3.callback = self.one

        self.add_item(self.button1)
        self.add_item(self.button2)
        self.add_item(self.button3)

    def init(self, msg):
        self.original_message = msg

    async def first(self, interaction):
        await interaction.response.defer()
        await self.original_message.edit("처음 곡부터 추가합니다.", view=None)
        await self.music.list(self.ctx, self.url, msg=self.original_message)

    async def current(self, interaction):
        await interaction.response.defer()
        await self.original_message.edit("현재 곡부터 추가합니다.", view=None)
        await self.music.list(self.ctx, self.url, current=True, msg=self.original_message)

    async def one(self, interaction):
        await interaction.response.defer()
        await self.original_message.edit("한 곡만 추가합니다.")
        await self.music.queue(self.ctx, self.url.split("&list=")[0], msg=self.original_message)

class SearchView(View):
    def __init__(self, ctx, data, music):
        super().__init__(timeout=None)
        self.page = 0
        self.ctx = ctx
        self.data = data
        self.music = music
        self.original_message = None

        self.button_prev = Button(style=ButtonStyle.primary, label="이전", custom_id="prev", emoji="⬅️")
        self.button_next = Button(style=ButtonStyle.primary, label="다음", custom_id="next", emoji="➡️")
        self.button_add = Button(style=ButtonStyle.green, label="추가", custom_id="add", emoji="⤴️")
        self.button_cancel = Button(style=ButtonStyle.red, label="취소", custom_id="cancel", emoji="⤵️")

        self.button_prev.callback = self.prev
        self.button_next.callback = self.next
        self.button_add.callback = self.add
        self.button_cancel.callback = self.cancel

        self.add_item(self.button_prev)
        self.add_item(self.button_next)
        self.add_item(self.button_add)
        self.add_item(self.button_cancel)

    async def init(self, interaction):
        if self.original_message is None:
            self.original_message = await interaction.channel.fetch_message(interaction.message.id)

    async def embed(self):
        embed = Embed(title=self.data['title'][self.page], url=self.data['url'][self.page])
        embed.set_image(url=self.data['thumbnail'][self.page])
        await self.original_message.edit(embed=embed)


    async def prev(self, interaction):
        await interaction.response.defer()
        await self.init(interaction)
        if self.page == 0:
            self.page = 4
        else:
            self.page -= 1

        await self.embed()

    async def next(self, interaction):
        await interaction.response.defer()
        await self.init(interaction)
        if self.page == 4:
            self.page = 0
        else:
            self.page += 1

        await self.embed()

    async def add(self, interaction):
        await interaction.response.defer()
        await self.init(interaction)
        # await self.original_message.delete()
        await self.music.queue(self.ctx, self.data['url'][self.page], self.original_message)

    async def cancel(self, interaction):
        await interaction.response.defer()
        await self.init(interaction)
        await self.original_message.delete()

        
class playControlPanel(View):
    def __init__(self, ctx, music):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.music = music
        self.pauseButtonView = Button(style=ButtonStyle.gray, label="일시정지", custom_id="pause", emoji="⏸️")
        self.resumeButtonView = Button(style=ButtonStyle.green, label="다시재생", custom_id="resume", emoji="▶️")

        self.prevButton = Button(style=ButtonStyle.gray, label="이전곡", custom_id="prev", emoji="⏮️", disabled=True if self.music.current == 0 else False)
        self.pauseButton = self.pauseButtonView
        self.skipButton = Button(style=ButtonStyle.gray, label="다음곡", custom_id="skip", emoji="⏭️")
        self.stopButton = Button(style=ButtonStyle.danger, label="정지", custom_id="stop", emoji="⏹️")
        self.repeatButton = Button(style=ButtonStyle.gray, label="반복 안함", custom_id="repeat", emoji="➡️")

        self.init()

    def init(self):

        self.prevButton.callback = self.prev
        self.pauseButton.callback = self.pause
        self.skipButton.callback = self.skip
        self.stopButton.callback = self.stop
        self.repeatButton.callback = self.repeat

        self.add_item(self.prevButton)
        self.add_item(self.pauseButton)
        self.add_item(self.skipButton)
        self.add_item(self.stopButton)
        self.add_item(self.repeatButton)

    def initMsg(self, msg):
        self.msg = msg

    async def prev(self, interaction):
        await interaction.response.defer()
        await self.music.command_prev(self.ctx)

    async def pause(self, interaction):
        await interaction.response.defer(invisible=True)
        await self.music.command_pause(self.ctx)
        self.pauseButton.callback = self.resume
        self.pauseButton.label = "다시재생"
        self.pauseButton.style = ButtonStyle.green
        self.pauseButton.emoji = "▶️"
        await self.msg.edit(view=self)

    async def resume(self, interaction):
        await interaction.response.defer(invisible=True)
        await self.music.command_resume(self.ctx)
        self.pauseButton.callback = self.pause
        self.pauseButton.label = "일시정지"
        self.pauseButton.style = ButtonStyle.gray
        self.pauseButton.emoji = "⏸️"
        await self.msg.edit(view=self)

    async def skip(self, interaction):
        await interaction.response.defer()
        await self.music.command_skip(self.ctx)

    async def stop(self, interaction):
        await interaction.response.defer()
        await self.music.command_stop(self.ctx)

    async def repeat(self, interaction):
        await interaction.response.defer()
        # await self.music.repeat(self.ctx)