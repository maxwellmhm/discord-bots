import typing, discord, asyncio, yaml, aiohttp
from discord.ext import commands

class moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        #------------- YAML STUFF -------------#
        with open(r'files/config.yaml') as file:
            full_yaml = yaml.full_load(file)
            staff_roles = []
            guild = full_yaml['guildID']
            for roleid in full_yaml['StaffRoles']:
                staff_roles.append(self.bot.get_guild(guild).get_role(roleid))
        self.staff_roles = staff_roles
        self.yaml_data = full_yaml
        self.server = self.bot.get_guild(guild)
        self.console = self.bot.get_channel(full_yaml['ConsoleCommandsChannel'])

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

    async def namecheck(self, argument):
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f"https://api.mojang.com/users/profiles/minecraft/{argument}") as cs:
                if cs.status == 204: user = None
                elif cs.status == 400: user = None
                else:
                    res = await cs.json()
                    user = res["name"]
                return user

    # all the emoji are from the bots.gg discord server.
    # If your bot is in there, it'll be able to use them
    def get_user_badges(self, user):
        author_flags = user.public_flags
        flags = dict(author_flags)
        emoji_flags = ""
        if flags['staff'] is True:
            emoji_flags = f"{emoji_flags} <:staff:860644241800429639>"
        if flags['partner'] is True:
            emoji_flags = f"{emoji_flags} <:partnernew:860644259107569685>"
        if flags['hypesquad'] is True:
            emoji_flags = f"{emoji_flags} <:hypesquad:860644277687943208>"
        if flags['bug_hunter'] is True:
            emoji_flags = f"{emoji_flags} <:bughunter:585765206769139723>"
        if flags['hypesquad_bravery'] is True:
            emoji_flags = f"{emoji_flags} <:bravery:860644425319710760>"
        if flags['hypesquad_brilliance'] is True:
            emoji_flags = f"{emoji_flags} <:brilliance:860644445435199539>"
        if flags['hypesquad_balance'] is True:
            emoji_flags = f"{emoji_flags} <:balance:860644467933839410>"
        if flags['early_supporter'] is True:
            emoji_flags = f"{emoji_flags} <:supporter:860644501067268106>"
        if user.premium_since:
            emoji_flags = f"{emoji_flags} <:booster4:860644548887969832>"
        if flags['bug_hunter_level_2'] is True:
            emoji_flags = f"{emoji_flags} <:bughunter_gold:850843414953984041>" #not from bots.gg
        if flags['verified_bot_developer'] is True:
            emoji_flags = f"{emoji_flags} <:earlybotdev:850843591756349450>" #not from bots.gg
        if emoji_flags == "": emoji_flags = None
        return emoji_flags


    @commands.command(aliases = ['userinfo', 'ui'])
    async def uinfo(self, ctx, user: typing.Optional[discord.Member]):
        if not user: user = ctx.author
        # BADGES
        badges = self.get_user_badges(user)
        if badges: badges = f"\n<:store_tag:860644620857507901>**Badges:**{badges}"
        else: badges = ''
        # USERID
        userid = f"\n<:greyTick:860644729933791283>**ID:** `{user.id}`"
        # NICKNAME
        if user.nick: nick = f"\n<:nickname:850914031953903626>**Nickname:** `{user.nick}`"
        else: nick = ""
        # CREATION DATE
        date = user.created_at.strftime("%b %-d %Y at %-H:%M")
        created = f"\n<:invite:860644752281436171>**Created:** `{date} UTC`"
        # JOIN DATE
        if user.joined_at:
            date = user.joined_at.strftime("%b %-d %Y at %-H:%M")
            joined = f"\n<:joined:849392863557189633>**joined:** `{date} UTC`"
        else: joined = ""
        # GUILD OWNER
        if user is ctx.guild.owner:
            owner = f"\n<:owner:860644790005399573>**Owner:** <:check:314349398811475968>"
        else: owner = ""
        # BOT
        if user.bot:
            bot = f"\n<:botTag:860645571076030525>**Bot:** <:check:314349398811475968>"
        else: bot = ""
        # BOOSTER SINCE
        if user.premium_since:
            date = user.premium_since.strftime("%b %-d %Y at %-H:%M")
            boost = f"\n<:booster4:860644548887969832>**Boosting since:** `{date} UTC`"
        else: boost = ""

        # Join Order
        order = f"\n<:moved:848312880666640394>**Join position:** `{sorted(ctx.guild.members, key=lambda user: user.joined_at).index(user) + 1}`"

        if user.premium_since:
            date = user.premium_since.strftime("%b %-d %Y at %-H:%M")
            boost = f"\n<:booster4:860644548887969832>**Boosting since:** `{date} UTC`"
        else: boost = ""
        # ROLES
        roles = ""
        for role in user.roles:
            if role is ctx.guild.default_role: continue
            roles = f"{roles} {role.mention}"
        if roles != "":
            roles = f"\n<:role:860644904048132137>**roles:** {roles}"
        # EMBED
        embed = discord.Embed(color=ctx.me.color, description=f"""{badges}{owner}{bot}{userid}{created}{nick}{joined}{order}{boost}{roles}""")
        embed.set_author(name=user, icon_url=f"https://raw.githubusercontent.com/LeoCx1000/discord-bots/master/images/{user.status}.png")
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)



#------------------------------------------------------------#
#------------------------ KICK ------------------------------#
#------------------------------------------------------------#

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to kick')
            return
        elif member == ctx.author:
            await self.error_message(ctx, 'You can\'t kick yourself')
            return
        elif member.top_role >= ctx.me.top_role:
            await self.error_message(ctx, 'I\'m not high enough in role hierarchy to kick that member!')
            return
        if member.top_role <= ctx.author.top_role:
            if member.guild_permissions.ban_members == False or member.guild_permissions.kick_members == False:
                try:
                    mem_embed=discord.Embed(description=f"**{ctx.message.author}** has kicked you from **{ctx.guild.name}**", color=ctx.me.color)
                    if reason: mem_embed.set_footer(text=f'reason: {reason}')
                    await member.send(embed=mem_embed)
                    await member.kick(reason=reason)
                    if reason:
                        embed=discord.Embed(description=f"""{ctx.author.mention} kicked {member.mention}
```reason: {reason}```""", color=ctx.me.color)
                    else:
                        embed=discord.Embed(description=f"""{ctx.author.mention} kicked {member.mention}""", color=ctx.me.color)
                    embed.set_footer(text=f'{member.id} | DM sent: ✅')
                    await ctx.send(embed=embed)
                except discord.HTTPException:
                    await member.kick(reason=reason)
                    if reason:
                        embed=discord.Embed(description=f"""{ctx.author.mention} kicked {member.mention}
```reason: {reason}```""", color=ctx.me.color)
                    else:
                        embed=discord.Embed(description=f"""{ctx.author.mention} kicked {member.mention}""", color=ctx.me.color)
                    embed.set_footer(text=f'{member.id} | DM sent: ❌')
                    await ctx.send(embed=embed)
            else:
                await self.error_message(ctx, 'you can\'t kick another moderator')
                return
        else:
            await self.error_message(ctx, 'Member is higher than you in role hierarchy')
            return

#-----------------------------------------------------------#
#------------------------ BAN ------------------------------#
#-----------------------------------------------------------#

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to ban')
            return
        elif member == ctx.author:
            await self.error_message(ctx, 'You can\'t ban yourself')
            return
        elif member.top_role >= ctx.me.top_role:
            await self.error_message(ctx, 'I\'m not high enough in role hierarchy to ban that member!')
            return
        if member.top_role <= ctx.author.top_role:
            if member.guild_permissions.ban_members == False or member.guild_permissions.kick_members == False:
                try:
                    mem_embed=discord.Embed(description=f"**{ctx.message.author}** has banned you from **{ctx.guild.name}**", color=ctx.me.color)
                    if reason: mem_embed.set_footer(text=f'reason: {reason}')
                    await member.send(embed=mem_embed)
                    await member.ban(reason=reason)
                    if reason:
                        embed=discord.Embed(description=f"""{ctx.author.mention} banned {member.mention}
```reason: {reason}```""", color=ctx.me.color)
                    else:
                        embed=discord.Embed(description=f"""{ctx.author.mention} banned {member.mention}""", color=ctx.me.color)
                    embed.set_footer(text=f'{member.id} | DM sent: ✅')
                    await ctx.send(embed=embed)
                except discord.HTTPException:
                    await member.ban(reason=reason)
                    if reason:
                        embed=discord.Embed(description=f"""{ctx.author.mention} banned {member.mention}
```reason: {reason}```""", color=ctx.me.color)
                    else:
                        embed=discord.Embed(description=f"""{ctx.author.mention} banned {member.mention}""", color=ctx.me.color)
                    embed.set_footer(text=f'{member.id} | DM sent: ❌')
                    await ctx.send(embed=embed)
            else:
                await self.error_message(ctx, 'you can\'t ban another moderator!')
                return

        else:
            await self.error_message(ctx, 'Member is higher than you in role hierarchy')
            return

#------------------------------------------------------------#
#------------------------ NICK ------------------------------#
#------------------------------------------------------------#

    @commands.command(aliases = ['sn', 'nick'])
    async def setnick(self, ctx, member : typing.Optional[discord.Member], *, new : typing.Optional[str] = 'None'):
        if member == None:
            if ctx.channel.permissions_for(ctx.author).manage_nicknames:
                await ctx.send("`!nick [member] (newNick)` - You must specify a member", delete_after=10)
                await asyncio.sleep(10)
                await ctx.message.delete()
            return
        if new == 'None':
            new = f'{member.name}'
        else:
            new = new
        old = f'{member.nick}'
        if old == 'None':
            old = f'{member.name}'
        else:
            old = old
        if member == ctx.author and ctx.channel.permissions_for(ctx.author).change_nickname:
            try:
                await member.edit(nick=new)
                await ctx.send(f"""✏ {ctx.author.mention} nick for {member}
**`{old}`** -> **`{new}`**""")
                try: await ctx.message.delete()
                except discord.Forbidden: return
            except discord.Forbidden:
                await self.error_message(ctx, 'Bot not high enough in role hierarchy')
                return
            except discord.HTTPException:
                await ctx.message.add_reaction('#️⃣')
                await ctx.message.add_reaction('3️⃣')
                await ctx.message.add_reaction('2️⃣')
                return
        elif ctx.channel.permissions_for(ctx.author).manage_nicknames:
            if member.top_role >= ctx.author.top_role:
                await self.error_message(ctx, "⚠ Cannot edit nick for members equal or above yourself!")
                return
            try:
                await member.edit(nick=new)
                await ctx.send(f"""✏ {ctx.author.mention} edited nick for **{member}**
**`{old}`** -> **`{new}`**""")
                try: await ctx.message.delete()
                except discord.Forbidden: return
            except discord.Forbidden:
                await self.error_message(ctx, 'Bot not high enough in role hierarchy')
                return
            except discord.HTTPException:
                await ctx.message.add_reaction('#️⃣')
                await ctx.message.add_reaction('3️⃣')
                await ctx.message.add_reaction('2️⃣')
        elif member == ctx.author and ctx.channel.permissions_for(ctx.author).change_nickname:
            await self.error_message(ctx, f"""You can only change your own nick!
> !nick {ctx.author.mention} `<new nick>`""")
            return
        else: await self.perms_error(ctx)

#-------------------------------------------------------------#
#------------------------ PURGE ------------------------------#
#-------------------------------------------------------------#

    @commands.command(aliases=['clean', 'purge', 'delete'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, argument: typing.Optional[int] = "noimput"):
        amount = argument
        if amount != "noimput":
            if amount <= 1000:
                await ctx.message.delete()
                await ctx.channel.purge(limit=amount)
                await ctx.send("🗑 Purge completed!", delete_after = 5)
            else:
                await ctx.message.delete()
                await ctx.channel.purge(limit=1000)
                await ctx.send("🗑 **[ERROR]** Applied limited of 1000 messages")
        else:
            await ctx.message.delete()
            await self.error_message(ctx, "Please specify amount of messages to purge!")

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure): await self.perms_error(ctx)

#------------------------------------------------------------#
#------------------------ MUTE ------------------------------#
#------------------------------------------------------------#

    @commands.command()
    async def mute(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to mute')
            return
        muterole = self.server.get_role(self.yaml_data['MuteRole'])
        if muterole in member.roles:
            await self.error_message(ctx, f'{member} is already muted')
            return
        try:
            await member.add_roles(muterole)
            mem_embed=discord.Embed(color=ctx.me.color)
            mem_embed.set_author(name=f"You've been muted by a staff member", icon_url='https://i.imgur.com/hKNGsMb.png')
            mem_embed.set_image(url='https://i.imgur.com/hXbvCT4.png')
            if reason: mem_embed.set_footer(text=f'reason: {reason}')
            await member.send(embed=mem_embed)
            if reason:
                embed=discord.Embed(description=f"""{ctx.author.mention} muted {member.mention} indefinitely...
```reason: {reason}```""", color=ctx.me.color)
            else:
                embed=discord.Embed(description=f"""{ctx.author.mention} muted {member.mention} indefinitely...""", color=ctx.me.color)
            await ctx.send(embed=embed)
        except:
            await self.error_message(ctx, 'something went wrong...')

#-------------------------------------------------------------#
#------------------------ UNMUTE -----------------------------#
#-------------------------------------------------------------#

    @commands.command()
    async def unmute(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to unmute')
            return
        muterole = ctx.guild.get_role(self.yaml_data['MuteRole'])
        if muterole not in member.roles:
            await self.error_message(ctx, f'{member} is not muted')
            return
        try:
            await member.remove_roles(muterole)
            mem_embed=discord.Embed(color=ctx.me.color)
            mem_embed.set_author(name=f"You've been unmuted by a staff member", icon_url='https://i.imgur.com/m1MtOVS.png')
            mem_embed.set_image(url='https://i.imgur.com/23XECtg.png')
            if reason: mem_embed.set_footer(text=f'reason: {reason}')
            await member.send(embed=mem_embed)
            if reason:
                embed=discord.Embed(description=f"""{ctx.author.mention} unmuted {member.mention}
```reason: {reason}```""", color=ctx.me.color)
            else:
                embed=discord.Embed(description=f"""{ctx.author.mention} unmuted {member.mention}""", color=ctx.me.color)
            await ctx.send(embed=embed)
        except:
            await self.error_message(ctx, 'something went wrong...')

#---------------------------------------------------------------#
#------------------------ LOCKDOWN -----------------------------#
#---------------------------------------------------------------#

    @commands.command(aliases=['lock', 'ld'])
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, textchannel: typing.Optional[discord.TextChannel], *, reason = None):

        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return

        if not textchannel:
            await ctx.message.delete()
            textchannel = ctx.channel
        else:
            await ctx.message.add_reaction('🔓')

        perms = textchannel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = False

        if reason:
            await textchannel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f'locked by {ctx.author} - {reason}')
            embed=discord.Embed(description=f"{ctx.author.mention} has locked down {textchannel.mention} \n```reason: {reason}```", color=ctx.me.color)
        else:
            await textchannel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f'locked by {ctx.author}')
            embed=discord.Embed(description=f"{ctx.author.mention} has locked down {textchannel.mention}", color=ctx.me.color)
        await textchannel.send(embed=embed)

#-------------------------------------------------------------#
#------------------------ UNLOCK -----------------------------#
#-------------------------------------------------------------#

    @lockdown.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure): await self.perms_error(ctx)

    @commands.command(aliases=['unlock', 'uld'])
    @commands.has_permissions(manage_channels=True)
    async def unlockdown(self, ctx, textchannel: typing.Optional[discord.TextChannel], *, reason = None):

        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return

        if not textchannel:
            await ctx.message.delete()
            textchannel = ctx.channel
        else:
            await ctx.message.add_reaction('🔓')

        perms = textchannel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = True

        if reason:
            await textchannel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f'unlocked by {ctx.author} - {reason}')
            embed=discord.Embed(description=f"{ctx.author.mention} has unlocked {textchannel.mention} \n```reason: {reason}```", color=ctx.me.color)
        else:
            await textchannel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f'unlocked by {ctx.author}')
            embed=discord.Embed(description=f"{ctx.author.mention} has unlocked {textchannel.mention}", color=ctx.me.color)
        await textchannel.send(embed=embed)

    @unlockdown.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure): await self.perms_error(ctx)

#---------------------------------------------------------------#
#------------------------ GameBan ------------------------------#
#---------------------------------------------------------------#

    @commands.command(aliases=['smpban', 'gban'])
    async def GameBan(self, ctx, argument: typing.Optional[str] = 'invalid name', *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        name = await self.namecheck(argument)
        if name:
            if reason:
                await self.console.send(f'ban {name} {reason}')
                embed=discord.Embed(description=f"""{ctx.author.mention} banned **{name}** from the server
```reason: {reason}```""", color=ctx.me.color)
            else:
                await self.console.send(f'ban {name}')
                embed=discord.Embed(description=f"""{ctx.author.mention} banned **{name}** from the server""", color=ctx.me.color)
            await ctx.send(embed=embed)
        else:
            await self.error_message(ctx, 'That username is invalid!')

#-----------------------------------------------------------------#
#------------------------ GameUnban ------------------------------#
#-----------------------------------------------------------------#

    @commands.command(aliases=['smpunban', 'gunban'])
    async def GameUnban(self, ctx, argument: typing.Optional[str] = 'invalid name', *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        name = await self.namecheck(argument)
        if name:
            if reason:
                await self.console.send(f'unban {name}')
                embed=discord.Embed(description=f"""{ctx.author.mention} unbanned **{name}** from the server
```reason: {reason}```""", color=ctx.me.color)
            else:
                await self.console.send(f'unban {name}')
                embed=discord.Embed(description=f"""{ctx.author.mention} unbanned **{name}** from the server""", color=ctx.me.color)
            await ctx.send(embed=embed)
        else:
            await self.error_message(ctx, 'That username is invalid!')

#-------------------------------------------------------------#
#------------------------ VCBAN ------------------------------#
#-------------------------------------------------------------#

    @commands.command()
    async def vcban(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to VC-Ban')
            return
        vcbanrole = self.server.get_role(self.yaml_data['VcBanRole'])
        if vcbanrole in member.roles:
            await self.error_message(ctx, f'{member} is already VC-Banned')
            return
        try:
            await member.add_roles(vcbanrole)
            try: await member.move_to(None)
            except: pass
            mem_embed=discord.Embed(color=ctx.me.color)
            mem_embed.set_author(name=f"You've been VC-Banned by a staff member", icon_url='https://i.imgur.com/hKNGsMb.png')
            mem_embed.set_image(url='https://i.imgur.com/hXbvCT4.png')
            if reason: mem_embed.set_footer(text=f'reason: {reason}')
            await member.send(embed=mem_embed)
            if reason:
                embed=discord.Embed(description=f"""{ctx.author.mention} VC-Banned {member.mention} indefinitely...
```reason: {reason}```""", color=ctx.me.color)
            else:
                embed=discord.Embed(description=f"""{ctx.author.mention} VC-Banned {member.mention} indefinitely...""", color=ctx.me.color)
            await ctx.send(embed=embed)
        except:
            await self.error_message(ctx, 'something went wrong...')

#--------------------------------------------------------------#
#------------------------ UNVCBAN -----------------------------#
#--------------------------------------------------------------#

    @commands.command()
    async def vcunban(self, ctx, member: typing.Optional[discord.Member] = None, *, reason = None):
        if not any(role in self.staff_roles for role in ctx.author.roles):
            await self.perms_error(ctx)
            return
        if member == None:
            await self.error_message(ctx, 'You must specify a member to VC-Ban')
            return
        vcbanrole = ctx.guild.get_role(self.yaml_data['VcBanRole'])
        if vcbanrole not in member.roles:
            await self.error_message(ctx, f'{member} is not VC-Banned')
            return
        try:
            await member.remove_roles(vcbanrole)
            mem_embed=discord.Embed(color=ctx.me.color)
            mem_embed.set_author(name=f"You've been VC-Unbanned by a staff member", icon_url='https://i.imgur.com/m1MtOVS.png')
            mem_embed.set_image(url='https://i.imgur.com/23XECtg.png')
            if reason: mem_embed.set_footer(text=f'reason: {reason}')
            await member.send(embed=mem_embed)
            if reason:
                embed=discord.Embed(description=f"""{ctx.author.mention} VC-Unbanned {member.mention}
```reason: {reason}```""", color=ctx.me.color)
            else:
                embed=discord.Embed(description=f"""{ctx.author.mention} VC-Unbanned {member.mention}""", color=ctx.me.color)
            await ctx.send(embed=embed)
        except:
            await self.error_message(ctx, 'something went wrong...')



def setup(bot):
    bot.add_cog(moderation(bot))
