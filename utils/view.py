from discord.ui import Select, View, Button
from discord.ui.button import ButtonStyle
from discord import Embed

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

        
