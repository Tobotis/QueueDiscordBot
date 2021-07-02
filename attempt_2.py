import discord
import random
import os

QUEUES = {}
HELP_MESSAGE = """lol"""


class Queue:
    def __init__(self, queue_channel, manager_channel, queue, ):

        self.queue_channel = queue_channel
        self.manager_channel = manager_channel
        self.queue = queue
        self.random = False

    async def next(self, channel):
        print("Next person")
        if len(self.queue) == 0:
            await self.manager_channel.send(":pensive: Nobody in queue")
            return
        await self.rebuild_overview()
        if not random:
            for person in self.queue:
                if person in self.queue_channel.members:
                    await person.move_to(channel)
                    await self.manager_channel.send(":white_check_mark: Moved "+ person.name)
                    return
        else:
            random_member = self.queue[random.randint(0, len(self.queue) - 1)]
            await random_member.move_to(channel)
            await self.manager_channel.send(":white_check_mark: Moved " + random_member.name)

    async def toggle_random(self):
        self.random = not self.random
        await self.rebuild_overview()

    async def person_joined(self, member, ):
        if member != client.user:
            self.queue.append(member)
            print(member.name + " joined the queue")
            await self.rebuild_overview()

    async def person_left(self, member, ):
        if member in self.queue and member != client.user:
            self.queue.remove(member)
            print(member.name + " left the queue")
            await self.rebuild_overview()

    async def rebuild_overview(self):
        await self.manager_channel.send(
            embed=self.get_overview_embed())

    def get_overview_embed(self):
        embed = discord.Embed(title="Newest Queue", colour=discord.Colour(0xd02e1c),
                              description="**Random:**  " + (":white_check_mark:" if self.random else ":x:"))
        if len(self.queue) == 0:
            embed.add_field(name=":warning: ", value="Nobody waiting...")
        for person in self.queue:
            embed.add_field(
                name="**" + str(self.queue.index(person) + 1) + ".**  {}".format(person.name),
                value="\u200b", inline=False)
        return embed


class BotClient(discord.Client):

    async def on_ready(self):
        print("Initialization...")
        await client.change_presence(activity=discord.Activity(name=" !helpQ", type=discord.ActivityType.listening))
        for x in client.voice_clients:
            await x.move_to(None)
        print("Ready...")

    async def on_message(self, m):

        if m.author == client.user:
            return

        elif m.content.startswith("!initQ") or m.content.startswith("!initq"):
            print("Got !initQ command")
            if m.content[7:] != "":
                channel = discord.utils.get(m.guild.channels, name=m.content[7:])
                if channel is None:
                    await m.channel.send(":x: Could not find the given channel")
                    return
                elif not isinstance(channel, discord.VoiceChannel):
                    await m.channel.send(":x: The given channel is not a voice channel")
                    return

                elif channel.guild.id in QUEUES.keys():
                    if QUEUES[channel.guild.id] is not None:
                        if QUEUES[channel.guild.id].queue_channel == channel:
                            await m.channel.send(":x: The given channel is already a queue")
                            return
                        else:
                            await m.channel.send(":x: There is still a queue running on this server")
                            return

                people_waiting = []
                for member in channel.members:
                    if member != client.user:
                        people_waiting.append(member)
                QUEUES[m.guild.id] = Queue(channel, m.channel, people_waiting, )
                await QUEUES[m.guild.id].rebuild_overview()
                await channel.connect()
                await m.channel.send(
                    ":white_check_mark: The channel `{}` turned into a queue".format(channel.name))
            else:
                await m.channel.send(":x: Please provide a channel `!initQ [CHANNEL NAME]`")

        elif m.content.startswith("!togglerandom"):
            if m.channel.guild.id in QUEUES.keys():
                print("Got !togglerandom command")
                await QUEUES[m.guild.id].toggle_random()
                await m.channel.send(":twisted_rightwards_arrows: Randomize" + (
                    " on :white_check_mark:" if QUEUES[m.guild.id].random else " off :x:"))
            else:
                await m.channel.send(":x: Please initiate a queue before changing settings")
        elif m.content.startswith("!endQ") or m.content.startswith("!endq"):
            print("Got !endQ command")
            if m.channel.guild.id in QUEUES.keys():
                if QUEUES[m.channel.guild.id] is not None:
                    for voice_client in client.voice_clients:
                        if voice_client.channel.guild == m.channel.guild:
                            await voice_client.move_to(None)
                    QUEUES[m.channel.guild.id] = None
                    await m.channel.send(":white_check_mark: Queue ended")
                else:
                    await m.channel.send(":x: There is no queue running")
            else:
                await m.channel.send(":x: There is no queue running")

        elif m.content.startswith("!helpQ") or m.content.startswith("!helpq"):
            print("Got !helpQ command")
            await m.channel.send(HELP_MESSAGE)

    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            if member == client.user and after.channel is not None:
                if after.channel.guild.id in QUEUES.keys():
                    if after.channel != QUEUES[after.channel.guild.id].queue_channel:
                        print("Got moved into a room")
                        await QUEUES[after.channel.guild.id].next(after.channel)
                        await member.move_to(QUEUES[after.channel.guild.id].queue_channel)

            if after.channel is not None:
                if after.channel.guild.id in QUEUES.keys():
                    if QUEUES[after.channel.guild.id] is not None:
                        if after.channel == QUEUES[after.channel.guild.id].queue_channel:
                            await QUEUES[after.channel.guild.id].person_joined(member)

            if before.channel is not None:
                if before.channel.guild.id in QUEUES.keys():
                    if QUEUES[before.channel.guild.id] is not None:
                        if before.channel == QUEUES[before.channel.guild.id].queue_channel:
                            await QUEUES[before.channel.guild.id].person_left(member)


token = os.getenv("queuebottoken")
client = BotClient()
client.run(token)
