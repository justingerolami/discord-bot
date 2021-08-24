import os
import discord

# For loading discord token
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

client = discord.Client()


@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))



client.run(TOKEN)