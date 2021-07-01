import discord
from discord.ext import commands

QUEUES = []  # Keeps track of all queues which are running
KICK_EMOJI = "⏸"
NEXT_EMOJI = "⏬"


async def create_queue(message):
    name = str(message.content)[7:]
    already_used = False
    if name is None:
        await message.channel.send("No valid !startQ command: !startQ [queue title]")
        return
    for queue in QUEUES:
        if name.upper() == queue.category.name.upper()[7:]:
            already_used = True
    if already_used:
        await message.channel.send("The name is already in use :slight_frown:")
    else:
        queue = Queue(message.author)
        QUEUES.append(queue)
        await queue.setup(message)


class Queue:
    def __init__(self, host):
        self.waiting_people = []
        self.host = host
        self.manager_embed = None
        self.manager_channel = None
        self.queue_channel = None
        self.interview_channel = None
        self.role = None
        self.category = None

    async def setup(self, m):
        self.role = await m.channel.guild.create_role(name="QUEUE " + m.content[8:])
        await self.host.add_roles(self.role)
        for guild in client.guilds:
            if guild == m.channel.guild:
                member = guild.get_member(client.user.id)
                await member.add_roles(self.role)
                break

        await self.setup_category(m)
        await self.rebuild_manager()

    async def setup_category(self, message):
        self.category = await message.guild.create_category(
            "QUEUE " + message.content[7:])
        for role in message.guild.roles:
            await self.category.set_permissions(role, send_messages=False, add_reactions=False, connect=False, )
        await self.category.set_permissions(self.role, add_reactions=True, connect=True, send_messages=True, )

        self.manager_channel = await self.category.create_text_channel(
            "manager")

        self.interview_channel = await self.category.create_voice_channel(
            "interview")

        self.queue_channel = await self.category.create_voice_channel(
            "queue")

        for role in message.guild.roles:
            if role is not self.role:
                await self.queue_channel.set_permissions(role, speak=False, connect=True)

    async def rebuild_manager(self):
        if self.manager_embed is not None:
            await self.manager_embed.delete()
            self.manager_embed = None
        message = await self.manager_channel.send(
            embed=self.get_manager_embed())

        self.manager_embed = message

        await self.add_reactions_to_manager_embed()

    def get_manager_embed(self):
        embed = discord.Embed(title="Queue Management", colour=discord.Colour(0xd02e1c))
        if len(self.waiting_people) == 0:
            embed.add_field(name="Nobody waiting...", value="Try to motivate someone to talk with you")
        for person in self.waiting_people:
            embed.add_field(name=str(self.waiting_people.index(person) + 1), value=person.name)
        embed.set_footer(text="Manage by reacting to this message")
        return embed  # Return the embed

    async def add_reactions_to_manager_embed(
            self):
        await self.manager_embed.add_reaction(NEXT_EMOJI)
        await self.manager_embed.add_reaction(KICK_EMOJI)

    async def handle_message(self, m):
        if m.author is self.host:
            if m.content.startswith("!endQ") or m.content.startswith("!endq"):
                for channel in self.category.channels:
                    await channel.delete()
                await self.role.delete()
                await self.category.delete()
                QUEUES.remove(self)
            elif m.content.startswith("!next"):
                await self.next_person()
            elif m.content.startswith("!kick"):
                await self.next_person(only_kick=True)

    async def handle_reaction(self, reaction, user):
        if reaction.message == self.manager_embed and user == self.host:
            if reaction.emoji == NEXT_EMOJI:
                await self.next_person()
            elif reaction.emoji == KICK_EMOJI:
                await self.next_person(only_kick=True)

        elif reaction.message == self.manager_embed and user != client.user:
            await reaction.message.channel.send(":x: You don't have the permission to manage :x:")

    async def next_person(self, only_kick=False):
        for member in self.interview_channel.members:
            if member is not self.host:
                await member.move_to()
        if not only_kick:
            for member in self.waiting_people:
                if member in self.queue_channel.members:
                    await member.move_to(self.interview_channel)
                    await self.rebuild_manager()
                    return
            await self.manager_channel.send("Nobody waiting...")

    async def person_joined(self, member, ):
        self.waiting_people.append(member)
        await self.rebuild_manager()

    async def person_left(self, member, ):
        self.waiting_people.remove(member)
        await self.rebuild_manager()


class BotClient(discord.Client):
    async def on_ready(self):
        print("Initialization...")
        guilds = client.guilds
        for guild in guilds:
            cats = guild.categories
            for cat in cats:
                if cat.name.startswith("QUEUE "):
                    for channel in cat.channels:
                        await channel.delete()
                    await cat.delete()
            roles = guild.roles
            for role in roles:
                if role.name.startswith("QUEUE "):
                    await role.delete()

    async def on_message(self, m):
        if m.author == client.user:
            return
        elif m.content.startswith("!startQ ") or m.content.startswith("!startq "):
            await create_queue(m)
        for queue in QUEUES:
            if m.channel.category == queue.category:
                await queue.handle_message(m)

    async def on_voice_state_update(self, member, before, after):
        for queue in QUEUES:
            if after.channel is queue.queue_channel:
                print("New person")
                await queue.person_joined(member)
            elif before.channel is queue.queue_channel:
                await queue.person_left(member)

    async def on_reaction_add(self, reaction, user):
        for queue in QUEUES:
            if reaction.message.channel.category == queue.category:
                await queue.handle_reaction(reaction, user)


client = BotClient()
client.run("")
