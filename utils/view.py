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
        embed = Embed(title=self.data[self.page * 2 + 1], url=f"https://www.youtube.com/watch?v={self.data[self.page*2]}")
        embed.set_image(url=f"https://i.ytimg.com/vi/{self.data[self.page*2]}/hqdefault.jpg")
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
        await self.music.queue(self.ctx, f"https://www.youtube.com/watch?v={self.data[self.page*2]}", self.original_message)

    async def cancel(self, interaction):
        await interaction.response.defer()
        await self.init(interaction)
        await self.original_message.delete()

        
