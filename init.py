import os
import discord
import member_functions as mf
from sqlalchemy import create_engine

# For loading discord token
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

TOKEN = os.getenv('TOKEN')
NOBLES = os.getenv('NOBLES')
MODS = os.getenv('MODERATORS')
ADMIN = os.getenv('ADMIN')
url = os.getenv('url')

client = discord.Client()
db = create_engine(url, echo = False)

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


@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.startswith('$length'):
		username = message.content[8:]
		try:
			#connect to the database
			conn = db.connect()

			#query for the joined date and the age of the user
			result = conn.execute("SELECT joined, AGE(joined) FROM members WHERE LOWER(username) = LOWER('{username}')".format(username=username)).fetchone()

			#convert to nice format
			niceJoinedDate = result[0].strftime('%b %d, %Y')
			numDays = result[1].days

			#Calculate the rank and days until promotion
			rank,daysUntilRank = mf.calculate_rank(numDays)

			if daysUntilRank == -1:
				rankMsg = "You have reached the highest rank!"
			else:
				rankMsg = "Your next promotion is in " + str(daysUntilRank) + " days!"

			#send message to the channel
			await message.channel.send('{name}, you\'ve been a member for {days} days. You Joined on {joinedDate}.\n'\
			 							'Your rank should be {currentRank}!\n'\
			 							'{rankMsg}'.format(name=username,days=numDays, joinedDate=niceJoinedDate, currentRank=rank, rankMsg=rankMsg))
			conn.close()

		except Exception as e:
			await message.channel.send('Username not found. Please enter the name when you applied.')
			print(e)



	if message.content.startswith('$updatename'):
		msg = message.content[12:]

		#split the input message to get old and new names
		result = [x.strip() for x in msg.split(',')]

		#user entered the command properly
		if len(result) == 2:
			oldname = result[0]
			newname = result[1]

			conn = db.connect()

			#Query to see if record exists
			if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{oldname}'))".format(oldname=oldname)).fetchone()[0] == True:
				#query to update the name
				result = conn.execute("UPDATE members SET username = '{newname}' WHERE LOWER(username) = LOWER('{oldname}')".format(newname=newname, oldname=oldname))
				await message.channel.send('Updated username from {oldname} to {newname}'.format(oldname=oldname,newname=newname))
			else:
				await message.channel.send('Username not found. Please enter the name when you applied.')
			conn.close()
			
		else:
			# Needs more/less fields
			await message.channel.send('Error: You need to add {0} fields, meaning it can only have {1} comma.'\
				' For example: $update oldname,newname'.format(2,1))
client.run(TOKEN)
db.dispose()