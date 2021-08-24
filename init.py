import os
import discord

# For loading discord token
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

TOKEN = os.getenv('TOKEN')
NOBLES = os.getenv('NOBLES')
MODS = os.getenv('MODERATORS')
ADMIN = os.getenv('ADMIN')

client = discord.Client()

# When the bot connects to Discord
@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))


# When a new member joins, send DM instructing them to apply
@client.event
async def on_member_join(member):
	await member.create_dm()
	await member.dm_channel.send(
		("Welcome to Noble Bros, {member_name}! If you wish to officially join and participate in clan events,"\
		" please fill out the clan app by typing '%apply' (without the quotation) here: <#638099028365672448>."\
		" Please change your server nickname to match your rsn by clicking the arrow beside"\
		" noble bros 2.0' -> 'change nickname'."\
		" If you have any questions, please message one of the admins listed under 'member list'.").format(member_name=member.mention))


client.run(TOKEN)