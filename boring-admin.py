import os

import discord
from discord import Member, Message
from discord.ext.commands import Bot, has_role
from discord.ext.commands.errors import CommandError, MissingRole
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = Bot(command_prefix='R', intents=intents)

# Command variables
use_autorole = True

use_logging = True
logging_channel = 1060665813968892035 # customise

admin_role = 1060641431347281931

# Utility
async def log(message: str, ignore_state: bool = False):
    if use_logging or ignore_state:
        await bot.get_channel(logging_channel).send(message)

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

    else:
        await bot.process_commands(message)

@bot.event
async def on_message_edit(beforeMessage: Message, afterMessage: Message):
    if afterMessage.channel.name == 'gn':
        if afterMessage.content != 'gn':
            await afterMessage.delete()

    if afterMessage.channel.name == 'gm':
        if afterMessage.content != 'gm':
            await afterMessage.delete()

@bot.event
async def on_command_error(error: CommandError, ctx: Message):
    # Ignore known errors
    if isinstance(error, MissingRole):
        pass

@bot.event
async def on_member_join(member: Member):
    if use_autorole:
        role = get(member.guild.roles, name="Member")

        await member.add_roles(role)

# Admin commands
@bot.command()
@has_role(admin_role)
async def toggle_autorole(ctx: Message):
    global use_autorole
    use_autorole = not use_autorole

    await log(f"✅ AutoRole is now {'disabled' if not use_autorole else 'enabled'}!")

@bot.command()
@has_role(admin_role)
async def toggle_logging(ctx: Message):
    global use_logging
    use_logging = not use_logging

    # Override state to inform either way
    await log(f"✅ Logging is now {'disabled' if not use_logging else 'enabled'}!", True)

bot.run(os.getenv('TOKEN'))
