import discord, asyncio, typing, re, yaml, datetime
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

class modmail(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        #------------- YAML STUFF -------------#
        with open(r'files/config.yaml') as file:
            full_yaml = yaml.full_load(file)
            staff_roles = []
            for roleid in full_yaml['StaffRoles']:
                staff_roles.append(self.bot.get_guild(full_yaml['guildID']).get_role(roleid))
        self.staff_roles = staff_roles
        self.yaml_data = full_yaml

    #--------------- FUNCTIONS ---------------#

    async def perms_error(self, ctx):
        await ctx.message.add_reaction('🚫')
        await asyncio.sleep(self.yaml_data['ReactionTimeout'])
        try:
            await ctx.message.delete()
            return
        except: return

    async def error_message(self, ctx, message):
        embed = discord.Embed(color=ctx.me.color)
        embed.set_author(name=message, icon_url='https://i.imgur.com/OAmzSGF.png')
        await ctx.send(embed=embed, delete_after=self.yaml_data['ErrorMessageTimeout'])
        await asyncio.sleep(self.yaml_data['ErrorMessageTimeout'])
        try:
            await ctx.message.delete()
            return
        except: return



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild: return
        if message.author == self.bot.user: return
        if message.content.startswith('.'):
            await message.channel.send('⚠ messages starting with `.` will not be sent ⚠', delete_after=5)
            return
        channel = self.bot.get_channel(self.yaml_data['ModMailChannel'])
        embed = discord.Embed(color=0xD7342A)
        if message.content:
            embed.add_field(name=f'<:incomingarrow:848312881070080001> **{message.author}**', value=f'{message.content}')
        else:
            embed.add_field(name=f'<:incomingarrow:848312881070080001> **{message.author}**', value=f'_ _')
        embed.set_footer(text=f'.dm {message.author.id}')
        if message.attachments:
            file = message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            elif spoiler:
                embed.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
            else:
                embed.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)
        await channel.send(embed=embed)
        await message.add_reaction('📬')
        await asyncio.sleep(2.5)
        await message.remove_reaction('📬', self.bot.user)

    @commands.command(aliases=['pm', 'message', 'direct'])
    @commands.has_permissions(manage_messages=True)
    async def dm(self, ctx, member: typing.Optional[discord.Member], *, message = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await ctx.message.add_reaction('⁉')
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        channel = self.bot.get_channel(self.yaml_data['ModMailChannel'])
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            if ctx.message.attachments:
                file = ctx.message.attachments[0]
                myfile = await file.to_file()
                embed = discord.Embed(color=0x47B781)
                if message:
                    embed.add_field(name=f'<:outgoingarrow:848312880679354368> **{member.name}#{member.discriminator}**', value=message)
                    await member.send(message, file=myfile)
                else:
                    embed.add_field(name=f'<:outgoingarrow:848312880679354368> **{member.name}#{member.discriminator}**', value='_ _')
                    await member.send(file=myfile)
                if ctx.message.attachments:
                    file = ctx.message.attachments[0]
                    spoiler = file.is_spoiler()
                    if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                        embed.set_image(url=file.url)
                    elif spoiler:
                        embed.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
                    else:
                        embed.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)
                embed.set_footer(text=f'.dm {member.id}')
                await channel.send(embed=embed)
            else:
                await member.send(message)
                embed = discord.Embed(color=0x47B781)
                embed.add_field(name=f'<:outgoingarrow:848312880679354368> **{member.name}#{member.discriminator}**', value=message)
                embed.set_footer(text=f'.dm {member.id}')
                await channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"{member}'s DMs are closed.")

    @commands.command(aliases=['spm', 'smessage', 'sdirect'])
    @commands.has_permissions(manage_messages=True)
    async def sdm(self, ctx, member: typing.Optional[discord.Member], *, message = ""):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await ctx.message.add_reaction('⁉')
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        await ctx.message.delete()
        try:
            if ctx.message.attachments:
                file = ctx.message.attachments[0]
                myfile = await file.to_file()
                await member.send(message, file=myfile)
                embed = discord.Embed(color=0x47B781)
            else:
                await member.send(message)
        except discord.Forbidden:
            await ctx.send(f"{member}'s DMs are closed.")

    @sdm.error
    async def dm_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.message.add_reaction('🚫')
            await asyncio.sleep (5)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def massping(self, ctx, user: typing.Optional[discord.Member], amount:typing.Optional[int]):
        if user == None or amount == None: return
        if amount >= 15: amount = 15
        i = 0
        while i < amount:
            await ctx.send(user.mention, delete_after=1.5)
            i = i+1
            await asyncio.sleep(1.5)

def setup(bot):
    bot.add_cog(modmail(bot))
