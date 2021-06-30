import discord

QUEUES = []  # Keeps track of all queues which are running


async def create_queue(message):  # Create a new Queue
    name = str(message.content)[7:]  # Get the name of the queue
    already_used = False  # True if the name is already in use
    if name is None:
        await message.channel.send("No valid !startQ command: !startQ [queue title]")  # Send an explanation
        return
    for queue in QUEUES:  # Iterate through all the current queues
        if name.upper() == queue.category.name.upper()[7:]:  # Check if the name is the same
            already_used = True
    if already_used:  # Check if the name is already in use
        await message.channel.send("The name is already in use :slight_frown:")  # Send an explanation
    else:  # Create a new queue
        queue = Queue(message.author)  # Instantiate a new Queue
        QUEUES.append(queue)  # Add it in the list of the current queues
        await queue.setup(message)  # Setup the queue


class Queue:  # Queue class (instantiated for every Queue)
    def __init__(self, host, bot_role):
        self.waiting_people = []
        self.host = host
        self.manager_embed = None
        self.manager_channel = None
        self.bot_role = bot_role
        self.role = None
        self.category = None

    async def setup(self, m):  # Takes a message and setups the queue
        self.role = await m.channel.guild.create_role(name="QUEUE " + m.content[8:])
        await self.setup_category(m)
        self.manager_channel = await self.category.create_text_channel(
            "manager")
        await self.host.add_roles(self.role)
        await self.rebuild_manager()

    async def setup_category(self, message):
        self.category = await message.guild.create_category(
            "QUEUE " + message.content[7:])  # Create the queue category with the name
        for role in message.channel.guild.roles:
            await self.category.set_permissions(role, send_messages=False, add_reactions=False, connect=False)
        await self.category.set_permissions(self.role, send_messages=True, add_reactions=True, connect=True)

    async def rebuild_manager(self):  # Displays the manager embed
        if self.manager_embed is not None:  # Check if the old manager embed should be deleted
            # and if there is an old one existing
            await self.manager_embed.delete()  # Delete the manager embed
            self.manager_embed = None
        message = await self.manager_channel.send(
            embed=self.get_manager_embed())  # Send the new embed in the manager channel

        self.manager_embed = message  # Set the new manager embed

        await self.add_reactions_to_game_manager_embed()  # Add the default reactions to the embed

    async def add_reactions_to_game_manager_embed(
            self):  # Add the default reactions to the embed, so its easier for the user to react
        await self.manager_embed.add_reaction("⏩")

    def get_manager_embed(self):  # Get the manager embed
        # Set the embed
        embed = discord.Embed(title="Queue Management", colour=discord.Colour(0xd02e1c))
        if len(self.waiting_people) == 0:
            embed.add_field(name="Nobody waiting...", value="Try to motivate someone to talk with you")

        embed.set_footer(text="Manage by reacting to this message")
        return embed  # Return the embed


class BotClient(discord.Client):  # Client class
    async def on_ready(self):  # Initialization
        print("Initialization...")
        guilds = client.guilds  # Get all the guilds of the bot
        for guild in guilds:  # Iterate through all the guilds
            cats = guild.categories  # Get all the categories of this guild
            for cat in cats:  # Iterate through all the categories in the guild
                if cat.name.startswith("QUEUE "):  # Check if the category is a QUEUE
                    for channel in cat.channels:  # Iterate through all the channels in this category
                        await channel.delete()  # Delete the channel
                    await cat.delete()  # Delete the category
            roles = guild.roles  # Get all the roles of the guild
            for role in roles:  # Iterate through all the roles in the guild
                if role.name.startswith("QUEUE "):  # Check if the role is a QUEUE role
                    await role.delete()  # Delete the role

    async def on_message(self, m):  # New Message

        try:
            if m.author == client.user:  # Check if the author of the message is the bot itself
                return
            elif m.content.startswith("!startQ ") or m.content.startswith("!startq "):  # Check for start command
                await create_queue(m)  # Start a new QUEUE Session

            for queue in QUEUES:  # Iterate through all the Queues on all servers
                if m.channel.category == queue.category:
                    await queue.handle_message(m)  # Handle a message for a specific queue
        except PermissionError:
            print("Permissions!!!")
            await m.channel.send("I need more permissions")



client = BotClient()
client.run("ODU5Nzk1NTMzMDQ3OTIyNzE4.YNx4_Q.NLGCH7vrbWDb87SdhRqrs8onBwM")
