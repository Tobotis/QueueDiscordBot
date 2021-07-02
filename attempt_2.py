import discord
import random
import os

QUEUES = {}  # Keeps track of all the queues at different servers
HELP_MESSAGE = """**USAGE:**
- **Commands**
    - **Commands in all channels**
        - `!helpQ` displays this paragraph
        - `!initQ [name of channel]` pick a channel to be the queue
        - `!endQ` ends the queue
        - `!togglerandom` sets the mode to random
- **Move the bot from queue to main channel to move the next person from queue**"""


async def init_queue(m):  # Initiates a queue
    if m.content[7:] != "":  # Check if a channel is provided
        channel = discord.utils.get(m.guild.channels, name=m.content[7:])  # Get the provided channel
        if channel is None:  # Check if the channel exists
            await m.channel.send(":x: Could not find the given channel")
            return
        elif not isinstance(channel, discord.VoiceChannel):  # Check if the channel is a voice channel
            await m.channel.send(":x: The given channel is not a voice channel")
            return
        elif channel.guild.id in QUEUES.keys():  # Check if there is a queue already running on the server
            await m.channel.send(":x: There is still a queue running on this server")
            return
        people_waiting = []  # List of the people already waiting in the channel
        for member in channel.members:  # Iterate people in the channel
            if member != client.user:  # Check if it is the bot itself
                people_waiting.append(member)  # Add the person to the people who are already waiting
        QUEUES[m.guild.id] = Queue(channel, m.channel, people_waiting)  # Instantiate a new queue
        await QUEUES[m.guild.id].rebuild_overview()  # Send the embed
        await channel.connect()  # Join the channel
        await m.channel.send(
            ":white_check_mark: The channel `{}` turned into a queue".format(channel.name))  # Send a completion message
    else:
        await m.channel.send(":x: Please provide a channel `!initQ [CHANNEL NAME]`")


class Queue:  # Queue class
    def __init__(self, queue_channel, manager_channel, queue):  # Constructor
        self.queue_channel = queue_channel  # Voice channel of queue
        self.manager_channel = manager_channel  # Channel to communicate
        self.queue = queue  # List of member in the queue
        self.random = False  # Randomizer

    async def next(self, channel):  # Next person has to be moved in the provided channel
        print("Next person")
        if len(self.queue) == 0:  # Check if the queue is empty
            await self.manager_channel.send(":pensive: Nobody in queue")  # Provide infromation
            return
        await self.rebuild_overview()  # Resend the embed
        if self.random:  # Check if mode is random
            print("Picking random")
            random_member = self.queue[random.randint(0, len(self.queue) - 1)]  # Pick a random person from the queue
            await random_member.move_to(channel)  # Move the person to the new channel
            await self.manager_channel.send(":white_check_mark: Moved " + random_member.name)  # Send completion message
        else:
            print("Picking not random")
            for person in self.queue:  # Iterate through all the waiting people
                if person in self.queue_channel.members:  # Pick the first one who is in the queue channel
                    await person.move_to(channel)  # Move the person to the new channel
                    await self.manager_channel.send(
                        ":white_check_mark: Moved " + person.name)  # Send completion message
                    return
                print("Skipped one")

    async def toggle_random(self):  # Change the randomizer mode
        self.random = not self.random
        await self.rebuild_overview()  # Rebuild the embed

    async def person_joined(self, member, ):
        if member != client.user:  # Check if the person who joined is not the bot
            self.queue.append(member)  # Add the person in the queue
            print(member.name + " joined the queue")
            await self.rebuild_overview()  # Resend the embed

    async def person_left(self, member, ):
        if member in self.queue and member != client.user:  # Check if the person who left is not the bot and is
            # still in queue
            self.queue.remove(member)  # Remove the person from the queue
            print(member.name + " left the queue")
            await self.rebuild_overview()  # Resend the embed

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


class BotClient(discord.Client):  # Client class

    async def on_ready(self):  # The bot is ready
        print("Initialization...")
        await client.change_presence(
            activity=discord.Activity(name=" !helpQ", type=discord.ActivityType.listening))  # Set the activity
        print("Ready...")

    async def on_message(self, m):  # Noticed a message
        if m.author == client.user:  # Check if it is from the bot itself => do nothing
            return
        elif m.content.startswith("!initQ") or m.content.startswith("!initq"):  # Check if its the !initQ command
            await init_queue(m)
        elif m.channel.guild.id in QUEUES.keys():  # Check if there is a queue running on the server
            if m.content.startswith("!togglerandom"):  # Check if its the !togglerandom command
                print("Got !togglerandom command")
                await QUEUES[m.guild.id].toggle_random()  # Switch the randomizer mode
                await m.channel.send(":twisted_rightwards_arrows: Randomize" + (
                    " on :white_check_mark:" if QUEUES[m.guild.id].random else " off :x:"))  # Send completion message
            elif m.content.startswith("!endQ") or m.content.startswith("!endq"):  # Check if its the !endQ command
                print("Got !endQ command")
                for voice_client in client.voice_clients:  # Iterate voice_clients of bot
                    if voice_client.channel.guild == m.channel.guild and voice_client.is_connected():  # Check if the
                        # voice client is connected at the current server
                        print("Disconnected voice client")
                        await voice_client.disconnect(None)  # Disconnect the voice client
                del QUEUES[m.channel.guild.id]  # Delete the running queue
                await m.channel.send(":white_check_mark: Queue ended")
        else:
            await m.channel.send(":x: There is no queue running")

        if m.content.startswith("!helpQ") or m.content.startswith("!helpq"):  # Check if its the !helpQ command
            print("Got !helpQ command")
            await m.channel.send(HELP_MESSAGE)  # Send the help message

    async def on_voice_state_update(self, member, before, after):  # Voice updated
        if before.channel != after.channel:  # Check if someone moved a channel

            if member == client.user and after.channel is not None:  # Check if the bot moved to a channel
                if after.channel.guild.id in QUEUES.keys():  # Check if its on a queue running server
                    if before.channel == QUEUES[after.channel.guild.id].queue_channel:  # Check if it got moved out
                        # of the queue channel
                        print("Got moved into another room")
                        await QUEUES[after.channel.guild.id].next(after.channel)  # Move the next person from queue
                        await member.move_to(QUEUES[after.channel.guild.id].queue_channel)  # Move the bot back to
                        # the queue channel

            if after.channel is not None:
                if after.channel.guild.id in QUEUES.keys():
                    if after.channel == QUEUES[after.channel.guild.id].queue_channel:  # Check if a person moved into
                        # the queue channel
                        await QUEUES[after.channel.guild.id].person_joined(member)  # Let the person join into the queue

            if before.channel is not None:
                if before.channel.guild.id in QUEUES.keys():
                    if before.channel == QUEUES[before.channel.guild.id].queue_channel:  # Check if a person left the
                        # queue channel
                        await QUEUES[before.channel.guild.id].person_left(member)  # Remove the person from the queue


token = os.getenv("queuebottoken")  # Get the token env-variable
client = BotClient()  # Instantiate the client class
client.run(token)  # Run the client with the token
