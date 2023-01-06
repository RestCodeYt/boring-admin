import asyncio
import json
import os
from typing import Optional

import discord
from discord import Color, Embed, Interaction, Member, Message, app_commands
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
logging_channel = 1060665813968892035 # customise

settings_file = 'settings.json'

# Default, before updating
settings = {
    'autorole': True,
    'logging': True
}

# Utility
def check_settings() -> None:
    global settings

    # Init first run
    if not os.path.isfile(settings_file):
        with open(settings_file, 'w') as f:
            f.write(json.dumps(settings))

    else:
        with open(settings_file, 'r') as f:
            settings = json.loads(f.read())

def save_settings() -> None:
    with open(settings_file, 'w') as f:
        f.write(json.dumps(settings))

async def log(message: str, ignore_state: bool = False) -> None:
    global settings

    if settings['logging'] or ignore_state:
        await bot.get_channel(logging_channel).send(message)

async def is_admin(interaction: Interaction) -> bool:
    role = discord.utils.find(lambda r: r.name == 'Admin', interaction.guild.roles)

    if not role in interaction.user.roles:
        await interaction.response.send_message('You aren\'t an admin!', ephemeral=True)
        return False
    return True

def create_embed(title: str, names: list, values: list) -> str:
    embed = Embed(title=title, color=Color.gold())

    for i, name in enumerate(names):
        embed.add_field(name=name, value=values[i])

    embed.set_footer(text='From your Boring Admin', icon_url='https://avatars.githubusercontent.com/u/118185179?v=4')
    
    return embed

def get_toggle_text(value: bool) -> str:
    return 'Enabled' if value else 'Disabled'

async def log_and_respond(interaction: Interaction, text: str) -> None:
    await log(text)

    await interaction.response.send_message(text, ephemeral=True)

# Events
@bot.event
async def on_ready():
    check_settings()
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
    global settings

    if settings['autorole']:
        role = get(member.guild.roles, name="Member")

        await member.add_roles(role)

# Admin commands
@bot.tree.command()
async def toggle_autorole(interaction: Interaction):
    if not await is_admin(interaction):
        return

    global settings
    settings['autorole'] = not settings['autorole']

    save_settings()

    log_msg = f"✅ Autorole is now {get_toggle_text(settings['autorole'])}!"
    
    await log(log_msg)

    await interaction.response.send_message(log_msg, ephemeral=True)

@bot.tree.command()
async def toggle_logging(interaction: Interaction):
    if not await is_admin(interaction):
        return

    global settings
    settings['logging'] = not settings['logging']

    save_settings()

    log_msg = f"✅ Logging is now {get_toggle_text(settings['logging'])}!"

    # Override state to inform either way
    await log(log_msg, True)

    await interaction.response.send_message(log_msg, ephemeral=True)

@bot.tree.command()
async def status(interaction: Interaction):
    if not await is_admin(interaction):
        return

    global settings

    names = ['AutoRole', 'Logging']
    values = [get_toggle_text(settings['autorole']), get_toggle_text(settings['logging'])]
    
    await interaction.response.send_message(embed=create_embed('Boring Admin options', names=names, values=values), ephemeral=True)

@bot.tree.command()
@app_commands.describe(
    member='The member to mute',
    minutes='The minutes to mute the member for',
    delete_count='Optional messages to delete from the muted member'
)
async def mute(interaction: Interaction, member: Optional[discord.Member] = None, minutes: int = 60, delete_count: int = 0):
    if not await is_admin(interaction):
        return
    
    if not member:
        await interaction.response.send_message('`member` is required!', ephemeral=True)
        return

    role = get(member.guild.roles, name="Muted")

    await member.add_roles(role)

    await log_and_respond(interaction, f'**{member.name}** has been muted for {minutes} minutes.')

    if delete_count > 0:
        async for message in member.history(limit=delete_count):
            await message.delete()

    # Pray it doesnt restart
    await asyncio.sleep(minutes * 60)

    await log(f'**{member.name}** has been unmuted.')

    await member.remove_roles(role)

bot.run(os.getenv('TOKEN'))
