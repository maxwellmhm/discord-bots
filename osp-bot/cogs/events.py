import json, random, typing, discord, asyncio, yaml, datetime, random
from discord.ext import commands

class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #------------- YAML STUFF -------------#
        with open(r'files/config.yaml') as file:
            full_yaml = yaml.full_load(file)
            mguild = self.bot.get_guild(full_yaml['guildID'])
        self.mguild = mguild
        self.yaml_data = full_yaml
        self.verified = mguild.get_role(full_yaml['RulesVerRole'])
        self.unverified = mguild.get_role(full_yaml['RulesUnvRole'])
        self.STLbefore = None
        self.ticket_staff = mguild.get_role(self.yaml_data['TicketStaffRole'])
        self.blackout = mguild.get_role(self.yaml_data['BlackoutRole'])
        self.ticket_log = self.bot.get_channel(full_yaml['TicketLogChannel'])

        with open(r'files/triggers.yaml') as triggers:
            trigger_words = yaml.full_load(triggers)
        self.trigger_words = trigger_words

    async def get_webhook(self, channel):
        hookslist = await channel.webhooks()
        if hookslist:
            for hook in hookslist:
                if hook.token:
                    return hook
                else: continue
        hook = await channel.create_webhook(name="OSP-Bot ticket logging")
        return hook

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if channel.guild.id != self.mguild.id: return
        await channel.set_permissions(self.blackout, view_channel = False, reason=f'automatic Blackout mode')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot: return
        if payload.channel_id == self.mguild.rules_channel.id:
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            mem = payload.member.id
            own = self.bot.get_guild(self.yaml_data['guildID']).owner_id

            if self.verified in payload.member.roles and mem != own and self.unverified not in payload.member.roles:
                await message.remove_reaction(payload.emoji, payload.member)
                return
            if mem != own:
                try: await message.remove_reaction(payload.emoji, payload.member)
                except: pass
            try: await payload.member.add_roles(self.verified)
            except: pass
            try: await payload.member.remove_roles(self.unverified)
            except: pass
            try: await self.bot.get_channel(860610324020592689).send(payload.member.mention, delete_after=0.1)
            except: pass

        elif str(payload.emoji) == "🚪":
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return
                try: await message.remove_reaction(payload.emoji, payload.member)
                except: pass

                embed=discord.Embed(color=0x47B781,
                                    description=f"""__Hey {payload.member.mention}, we see you're leaving this ticket.__

**Want to tell us why?**

You have 5 minutes to do so.""")

                embed.set_author(name=f"{payload.member} is leaving the ticket", icon_url=payload.member.avatar_url)
                embed.set_footer(text="Send \"no\" if you don't want to")
                lmsg = await message.channel.send(payload.member.mention, embed=embed)

                def check(m: discord.Message):  # m = discord.Message.
                    return m.author.id == payload.member.id and m.channel.id == message.channel.id

                try:
                    #                             event = on_message without on_
                    msg = await self.bot.wait_for(event = 'message', check = check, timeout = 300.0)
                    # msg = discord.Message
                except asyncio.TimeoutError:
                    # at this point, the check didn't become True, let's handle it.
                    err=discord.Embed(color=0xD7342A, description=f"**{payload.member} left the ticket.**")
                    await lmsg.edit(content=payload.member.mention, embed=err)
                else:
                    if msg.content.lower() == "no":
                        try: await msg.delete()
                        except: pass
                        err=discord.Embed(color=0xD7342A, description=f"**{payload.member} left the ticket.**")
                        await lmsg.edit(content=payload.member.mention, embed=err)
                    else:
                        try: await msg.delete()
                        except: pass
                        embed=discord.Embed(color=0xD7342A,
                                            description=f"""**{payload.member} left the ticket.**
**Reason:**
{msg.content}""")
                        await lmsg.edit(content=payload.member.mention, embed=embed)

                perms = message.channel.overwrites_for(payload.member)
                perms.send_messages = False
                perms.read_messages = False
                await message.channel.set_permissions(payload.member, overwrite=perms, reason=f"{payload.member.name} left ticket")
                #LOG
                TicketLog = await self.get_webhook(self.ticket_log)
                logemb = discord.Embed(color=0xD7342A, title=f"Left ticket #{message.channel.name}", description= f"""
{payload.member.mention} left ticket: {message.channel.mention}""")
                if msg:
                    if msg.content and msg.content.lower() != "no":
                        logemb.add_field(name="Reason:", value=msg.content)
                logemb.set_author(name=str(payload.member), icon_url=payload.member.avatar_url)
                await TicketLog.send(embed=logemb)

        elif str(payload.emoji) == "📁" and self.ticket_staff in payload.member.roles:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            archive = self.bot.get_channel(self.yaml_data['TicketsArchve'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return

                embed = message.embeds[0]
                embed.clear_fields()
                embed.add_field(name="Actions:", value="Archived! | 🗑 Delete (staff-only)")
                await message.edit(content=message.content, embed=embed)

                #LOG
                TicketLog = await self.get_webhook(self.ticket_log)
                logemb = discord.Embed(color=0x4286F4, title=f"Ticket #{message.channel.name} archived", description= f"""
                {payload.member.mention} archived {message.channel.name}""")
                logemb.set_author(name=str(payload.member), icon_url=payload.member.avatar_url)
                await TicketLog.send(embed=logemb)


                archive = self.bot.get_channel(self.yaml_data['TicketsArchve'])
                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    self.ticket_staff: discord.PermissionOverwrite(read_messages=True, manage_messages=False, send_messages=False)
                }
                await message.channel.edit(overwrites=overwrites, category=archive)
                await message.clear_reaction("📁")
                await message.channel.send("📁 This ticket is now archived")
                return


        elif str(payload.emoji) == "🔒" and self.ticket_staff in payload.member.roles:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return

                await message.add_reaction("✅")
                await message.add_reaction("❌")


        elif str(payload.emoji) == "✅" and self.ticket_staff in payload.member.roles:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                if not message.author.bot or "opened a ticket" not in message.content: return

                embed = message.embeds[0]
                embed.clear_fields()
                embed.add_field(name="Actions:", value="📁 Archive (staff-only) | 🗑 Delete (staff-only)")
                await message.edit(content=message.content, embed=embed)

                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    self.ticket_staff: discord.PermissionOverwrite(read_messages=True, manage_messages=True)
                }
                await message.channel.edit(overwrites=overwrites)
                await message.clear_reactions()
                await message.channel.send("🔐 This ticket is now locked")
                await message.add_reaction("📁")
                await message.add_reaction("🗑")

                #LOG
                TicketLog = await self.get_webhook(self.ticket_log)
                logemb = discord.Embed(color=0x4286F4, title=f"Ticket #{message.channel.name} closed", description= f"""
                {payload.member.mention} closed ticket: {message.channel.mention}""")
                logemb.set_author(name=str(payload.member), icon_url=payload.member.avatar_url)
                await TicketLog.send(embed=logemb)
                return

        elif str(payload.emoji) == "❌" and self.ticket_staff in payload.member.roles:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return
                await message.clear_reaction("✅")
                await message.clear_reaction("❌")
                await message.remove_reaction("🔒", payload.member)
                return

        elif str(payload.emoji) == "🗑" and self.ticket_staff in payload.member.roles:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            archive = self.bot.get_channel(self.yaml_data['TicketsArchve'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if archive.text_channels:
                for channel in archive.text_channels:
                    chids.append(channel.id)

            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return
                await message.channel.delete()
                #LOG
                TicketLog = await self.get_webhook(self.ticket_log)
                logemb = discord.Embed(color=0xD7342A, title=f"Ticket #{message.channel.name} deleted", description= f"""
                {payload.member.mention} deleted ticket {message.channel.mention}""")
                logemb.set_author(name=str(payload.member), icon_url=payload.member.avatar_url)
                await TicketLog.send(embed=logemb)
                return

        else:
            category = self.bot.get_channel(self.yaml_data['TicketsCategory'])
            chids = []
            if category.text_channels:
                for channel in category.text_channels:
                    chids.append(channel.id)
            if payload.channel_id in chids:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

                if not message.author.bot or "opened a ticket" not in message.content: return
                await message.remove_reaction(payload.emoji, payload.member)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.yaml_data['guildID']: return

        embed = discord.Embed(color = 0x0066ff,
                            description = f"""Welcome to the {member.guild.name}! You are the {sorted(member.guild.members, key=lambda user: member.joined_at).index(member) + 1} member. Please check out our <#860610050448031784> and agree to the {member.guild.rules_channel.mention} to gain access to the rest of the server. If you need anything, please message me, {self.bot.user.mention}, and our admin team will help you out! We hope you enjoy your time here.""",
                            timestamp = datetime.datetime.now(),
                            title = f"Welcome, {member}")

        embed.set_author(name = member.guild.name,
                        icon_url = member.guild.icon_url)

        embed.set_footer(text = "Member joined")

        await self.bot.get_channel(self.yaml_data['WelcomeChannel']).send(embed = embed)
        await self.bot.get_channel(self.yaml_data['JLLog']).send(f"""<:outgoingarrow:848312880679354368> **{member.name}#{member.discriminator}** joined **{member.guild.name}**!""")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != self.yaml_data['guildID']: return
        await self.bot.get_channel(self.yaml_data['JLLog']).send(f"""<:incomingarrow:848312881070080001> **{member.name}#{member.discriminator}** left **{member.guild.name}**!""")


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            channel = self.bot.get_channel(860633218829778954)
            underaged = before.guild.get_role(863187863038459924)
            overaged = before.guild.get_role(863187815340703755)
            if underaged in before.roles and overaged not in before.roles and overaged in after.roles and underaged not in after.roles:
                await channel.send(before.guild.owner.mention, embed=discord.Embed(
                color = 0xFF0000,
                description=f"""
<:suswell2:863246942853922836> **SUSPICIOUS MEMBER ACTIVITY NOTICED** <:maxwellsus2:863246342250692620>
*{before.mention} has changed their age status from {underaged.mention} to {overaged.mention}*
You might want to follow up on this.
"""
                ))
                self.STLbefore = before
                return

            elif overaged in before.roles and underaged not in before.roles and underaged in after.roles and overaged not in after.roles:
                await channel.send(before.guild.owner.mention, embed=discord.Embed(
                color = 0xFF0000,
                description=f"""
<:suswell2:863246942853922836> **SUSPICIOUS MEMBER ACTIVITY NOTICED** <:maxwellsus2:863246342250692620>
*{before.mention} has changed their age status from {overaged.mention} to {underaged.mention}*
You might want to follow up on this.
"""
))
                self.STLbefore = before
                return

            elif overaged in before.roles and underaged not in before.roles and underaged not in after.roles and overaged not in after.roles:
                self.STLbefore = before
                return

            elif underaged in before.roles and overaged not in before.roles and overaged not in after.roles and underaged not in after.roles:
                self.STLbefore = before
                return

            elif not self.STLbefore:
                self.STLbefore = before
                return

            if self.STLbefore.id != before.id:
                self.STLbefore = before
                return


            if underaged in self.STLbefore.roles and overaged not in self.STLbefore.roles and overaged in after.roles and underaged not in after.roles:
                await channel.send(before.guild.owner.mention, embed=discord.Embed(
                color = 0xFF0000,
                description=f"""
<:suswell2:863246942853922836> **SUSPICIOUS MEMBER ACTIVITY NOTICED** <:maxwellsus2:863246342250692620>
*{before.mention} has changed their age status from {underaged.mention} to {overaged.mention}*
You might want to follow up on this.
"""
                ))
                self.STLbefore = before
                return

            if overaged in self.STLbefore.roles and underaged not in self.STLbefore.roles and underaged in after.roles and overaged not in after.roles:
                await channel.send(before.guild.owner.mention, embed=discord.Embed(
                color = 0xFF0000,
                description=f"""
<:suswell2:863246942853922836> **SUSPICIOUS MEMBER ACTIVITY NOTICED** <:maxwellsus2:863246342250692620>
*{before.mention} has changed their age status from {overaged.mention} to {underaged.mention}*
You might want to follow up on this.
"""
))
                self.STLbefore = before
                return

################################################################################

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if message.channel.id in self.yaml_data['blackholes']:
            await message.delete()
            return
        ###DEPRESSION AND SUICIDAL EMBED DEFINITION###

        suicide_text = f"Hi, {message.author.mention}. If you need to talk to someone, please DM me and an admin will talk to you. Or, use a resource below. We all are here for you.:heart:"
        suicide_embed=discord.Embed(title="DEPRESSION AND SUICIDAL INTENTIONS", description="", color=0x0066ff)
        suicide_embed.add_field(name="National Suicide Prevention Lifeline", value="1-800-273-TALK (8255)", inline=False)
        suicide_embed.add_field(name="American Association of Suicidology", value="The [American Association of Suicidology](http://www.suicidology.org/) (AAS) promotes research, public awareness programs, public education and training for professionals and volunteers. AAS also serves as a national clearinghouse for information on suicide.", inline=False)
        suicide_embed.add_field(name="Depression Screening", value="The [Depression Screening](http://www.depression-screening.org/) website is sponsored by Mental Health America as part of the Campaign for America’s Mental Health. The mission of this website is to educate people about clinical depression, offer a confidential way for people to get screened for symptoms of depression and guide people toward appropriate professional help if necessary.", inline=False)
        suicide_embed.add_field(name="MoodGYM", value="[MoodGYM](http://www.moodgym.anu.edu.au/) has been evaluated in a scientific trial and found to be effective in relieving depression symptoms if people work through it systematically. This website uses cognitive behavioral therapy (CBT) methods to teach people to use ways of thinking that can help prevent depression.", inline=False)
        suicide_embed.add_field(name="Progressive Relaxation", value="[Download](http://www.hws.edu/studentlife/counseling_relax.aspx) two progressive relaxation tapes from the Hobart and William Smith Colleges website.", inline=False)
        suicide_embed.add_field(name="Suicide Prevention Resource Center", value="[The Suicide Prevention Resource Center](http://www.sprc.org/) has fact sheets on suicide by state and by population characteristics, as well as on many other subjects.", inline=False)

        ###NONSUICIDAL SELF-INJURY EMBED DEFINITION###

        self_injury_text = f"Hi, {message.author.mention}. If you need to talk to someone, please DM me and an admin will talk to you. Or, use a resource below. We all are here for you.:heart:"
        self_injury_embed=discord.Embed(title="NONSUICIDAL SELF-INJURY", description="", color=0x0066ff)
        self_injury_embed.add_field(name="Focus Adolescent Services", value="The [Focus Adolescent Services](http://www.focusas.com/) website is designed for parents and covers a wide range of mental health problems, including a section on self-injury.", inline=False)
        self_injury_embed.add_field(name="S.A.F.E. Alternatives (Self-Abuse Finally Ends)", value="[S.A.F.E. Alternatives](http://www.selfinjury.com/) is a residential treatment program for people who engage in self-injury. The website includes information about self-injury and about starting treatment. S.A.F.E information line: (Phone Word Acronym is a TW) ||1-800-DONT-CUT|| (1-800-366-8288)", inline=False)

        if "help" in message.content.lower() and self.bot.user in message.mentions:
            await message.channel.send(f"hello, {message.author.mention}! If you need assistance, please DM me and an admin will assist you!")


        #####  TRIGGERS.YAML STUFF #####

        # Triggers if any of the suicide_triggers in the triggers.yaml is said
        elif any(word in message.content.lower() for word in self.trigger_words['suicide_triggers']):
            # sends the suicide_embed defined above, with the suicide_text as the content
            await message.channel.send(suicide_text, embed=suicide_embed)

        # Triggers if any of the non_sudoku_triggers in the triggers.yaml is said
        elif any(word in message.content.lower() for word in self.trigger_words['non_sudoku_triggers']):
            # sends the self_injury_embed defined above, with the self_injury_text as the content
            await message.channel.send(self_injury_text, embed=self_injury_embed)

        # Triggers if the bot is pinged without context OR if the bot is quoted, and the message is less than 22 characters long.
        elif self.bot.user in message.mentions and message and len(message.content) <= 22 and not message.content.startswith("."):
            # gets the response from the list no_context_responses in triggers.yaml
            num = random.randint(0,100)
            if num <=30:
                response = random.choice(self.trigger_words['no_context_responses'])
                response = response.replace('%PING_USER%', f'{message.author.mention}')
                await message.channel.send(response)

        # Triggers if the bot is pinged with context
        elif self.bot.user in message.mentions and not message.content.startswith("."):
            # gets the response from the list context_responses in triggers.yaml
            num = random.randint(0,100)
            if num <=30:
                response = random.choice(self.trigger_words['context_responses'])
                response = response.replace('%PING_USER%', f'{message.author.mention}')
                await message.channel.send(response)

def setup(bot):
    bot.add_cog(events(bot))
