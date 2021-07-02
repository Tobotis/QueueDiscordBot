import discord
import random
import os

token = os.getenv("queuebottoken")
QUEUES = []  # Keeps track of all running queues
KICK_EMOJI = "⏹"
NEXT_EMOJI = "⏩"
NEXT_RANDOM_EMOJI = "🔀"
HELP_MESSAGE = """
    - **Commands**
        - **Commands in all channels**
            - `!helpQ` displays this message
            - `!startQ [name of queue]` hosts a new queue
        - **Commands in manager channel**
            - `!endQ` ends the queue and deletes everything
            - `!next` disconnects the current guest and moves in the next one of the queue
            - `!random` disconnects the current guest and moves in a random guest from the queue
            - `!kick` disconnects the current guest
    - **Reactions**
        - `⏩` disconnects the current guest and moves in the next one of the queue
        - `🔀` disconnects the current guest and moves in a random guest from the queue
        - `⏹` disconnects the current guest
        
    https://github.com/Tobotis/QueueDiscordBot
    """

async def create_queue(message):
    name = str(message.content)[7:]
    already_used = False
    print(name)
    if name is None or name == "":
        await message.channel.send("Please use:\n`!startQ [queue title]`")
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
            if role != self.role:
                await self.queue_channel.set_permissions(role, speak=False, connect=True)

    async def rebuild_manager(self):
        await self.manager_channel.purge()

        message = await self.manager_channel.send(
            embed=self.get_manager_embed())

        self.manager_embed = message
        try:
            await self.add_reactions_to_manager_embed()
        except Exception:
            print("Could not add reactions")

    def get_manager_embed(self):
        embed = discord.Embed(title="Queue Management", colour=discord.Colour(0xd02e1c))
        if len(self.waiting_people) == 0:
            embed.add_field(name=":warning: ", value="Nobody waiting...")
        for person in self.waiting_people:
            embed.add_field(
                name="**" + str(self.waiting_people.index(person) + 1) + ".**  {}".format(person.name),
                value="\u200b", inline=False)
        return embed  # Return the embed

    async def add_reactions_to_manager_embed(
            self):
        await self.manager_embed.add_reaction(NEXT_EMOJI)
        await self.manager_embed.add_reaction(NEXT_RANDOM_EMOJI)
        await self.manager_embed.add_reaction(KICK_EMOJI)

    async def handle_message(self, m):
        if m.author == self.host:
            if m.content.startswith("!endQ") or m.content.startswith("!endq"):
                print("ending queue")
                for channel in self.category.channels:
                    await channel.delete()
                await self.role.delete()
                await self.category.delete()
                QUEUES.remove(self)
            elif m.content.startswith("!next"):
                await self.next_person()
            elif m.content.startswith("!kick"):
                await self.next_person(only_kick=True)
            elif m.content.startswith("!random"):
                await self.next_person(randomize=True)

    async def handle_reaction(self, reaction, user):
        if reaction.message == self.manager_embed and user == self.host:
            if reaction.emoji == NEXT_EMOJI:
                await self.next_person()
            elif reaction.emoji == KICK_EMOJI:
                await self.next_person(only_kick=True)
                await self.rebuild_manager()
            elif reaction.emoji == NEXT_RANDOM_EMOJI:
                await self.next_person(randomize=True)

        elif reaction.message == self.manager_embed and user != client.user:
            await reaction.message.channel.send(":x: You are not the host {}".format(user.mention))

    async def next_person(self, only_kick=False, randomize=False):

        for member in self.interview_channel.members:
            if self.role not in member.roles:
                await member.move_to(None)

        if not only_kick:
            if len(self.waiting_people) == 0:
                await self.rebuild_manager()
                return
            elif randomize:
                random_member = self.waiting_people[random.randint(0, len(self.waiting_people) - 1)]
                await random_member.move_to(self.interview_channel)
                return
            else:
                for member in self.waiting_people:
                    if member in self.queue_channel.members:
                        await member.move_to(self.interview_channel)
                        return

    async def person_joined(self, member, ):
        self.waiting_people.append(member)
        await self.rebuild_manager()

    async def person_left(self, member, ):
        if member in self.waiting_people:
            self.waiting_people.remove(member)
            await self.rebuild_manager()


class BotClient(discord.Client):
    async def on_ready(self):
        await client.change_presence(activity=discord.Activity(name=" !helpQ", type=discord.ActivityType.watching))
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
        print("Message")
        if m.author == client.user:
            return
        elif m.content.startswith("!startQ") or m.content.startswith("!startq"):
            await create_queue(m)
        elif m.content.startswith("!helpQ") or m.content.startswith("!helpq"):
            await m.channel.send(HELP_MESSAGE)
        else:
            for queue in QUEUES:
                if m.channel == queue.manager_channel:
                    print("Handling message")
                    await queue.handle_message(m)

    async def on_voice_state_update(self, member, before, after):
        print("Voice state update")
        for queue in QUEUES:
            if after.channel == queue.queue_channel and before.channel != after.channel:
                print(member.name + " joined the queue")
                await queue.person_joined(member)
            elif before.channel == queue.queue_channel and before.channel != after.channel:
                print(member.name + " left the queue")
                await queue.person_left(member)

    async def on_reaction_add(self, reaction, user):
        for queue in QUEUES:
            if reaction.message.channel.category == queue.category:
                await queue.handle_reaction(reaction, user)


client = BotClient()
client.run(token)
