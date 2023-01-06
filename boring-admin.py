import os

import discord
from discord import Interaction, Member, Message, app_commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

MY_GUILD=discord.Object(id=1060640257420296314) # customise

class BoringAdmin(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

bot = BoringAdmin(intents=intents)

# Command variables
use_autorole = True

use_logging = True
logging_channel = 1060665813968892035 # customise

# Utility
async def log(message: str, ignore_state: bool = False):
    if use_logging or ignore_state:
        await bot.get_channel(logging_channel).send(message)

async def is_admin(interaction: Interaction):
    role = discord.utils.find(lambda r: r.name == 'Admin', interaction.guild.roles)

    if not role in interaction.user.roles:
        await interaction.response.send_message('You aren\'t an admin!', ephemeral=True)
        return False
    return True

# Events
@bot.event
async def on_ready():
    print('The Boring Admin bot is back to moderating..')

@bot.event
async def on_message(message: Message):
    # Self bot
    if message.author.id == bot.user.id:
        return

    # GM || GN channels
    # Only gm / gm, previous message mustn't be from the same user
    previous_messages: list[Message] = [message async for message in message.channel.history(limit=2)]
    has_previous_message = previous_messages[1].author.id == message.author.id if len(previous_messages) > 1 else False

    if message.channel.name == 'gn':
        if message.content != 'gn' or has_previous_message:
            await message.delete()

    elif message.channel.name == 'gm':
        if message.content != 'gm' or has_previous_message:
            await message.delete()

@bot.event
async def on_message_edit(beforeMessage: Message, afterMessage: Message):
    if afterMessage.channel.name == 'gn':
        if afterMessage.content != 'gn':
            await afterMessage.delete()

    elif afterMessage.channel.name == 'gm':
        if afterMessage.content != 'gm':
            await afterMessage.delete()

@bot.event
async def on_member_join(member: Member):
    if use_autorole:
        role = get(member.guild.roles, name="Member")

        await member.add_roles(role)

# Admin commands
@bot.tree.command()
async def toggle_autorole(interaction: Interaction):
    if not await is_admin(interaction):
        return

    global use_autorole
    use_autorole = not use_autorole

    log_msg = f"✅ Autorole is now {'disabled' if not use_autorole else 'enabled'}!"
    
    await log(log_msg)

    await interaction.response.send_message(log_msg, ephemeral=True)

@bot.tree.command()
async def toggle_logging(interaction: Interaction):
    if not await is_admin(interaction):
        return

    global use_logging
    use_logging = not use_logging

    log_msg = f"✅ Logging is now {'disabled' if not use_logging else 'enabled'}!"

    # Override state to inform either way
    await log(log_msg, True)

    await interaction.response.send_message(log_msg, ephemeral=True)

bot.run(os.getenv('TOKEN'))
