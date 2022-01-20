import os
import discord
import member_functions as mf
from sqlalchemy import create_engine
from datetime import datetime
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

#Github
TOKEN = os.environ['TOKEN']
url = os.environ['URL']

NOBLES = int(os.getenv('NOBLES'))
MODS = int(os.getenv('MODERATORS'))
ADMIN = int(os.getenv('ADMIN'))


reqRoles = [NOBLES,MODS,ADMIN]

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
		if len(message.content) >= 8:
			username = message.content[8:]
		else:
			username = ''
		discordID = message.author.id

		try:
			#connect to the database
			conn = db.connect()

			#query for the joined date and the age of the user
			result = conn.execute("SELECT username,joined, AGE(joined) FROM members WHERE LOWER(username) = LOWER('{username}') OR discordID = '{discordID}'".format(username=username, discordID=discordID)).fetchone()

			#convert to nice format
			dbusername = result[0]
			niceJoinedDate = result[1].strftime('%b %d, %Y')
			numDays = result[2].days

			#Calculate the rank and days until promotion
			rank,daysUntilRank = mf.calculate_rank(numDays)

			if daysUntilRank == -1:
				rankMsg = "You have reached the highest rank!"
			else:
				rankMsg = "Your next promotion is in " + str(daysUntilRank) + " days!"

			#send message to the channel
			await message.channel.send('{name}, you\'ve been a member for {days} days. You Joined on {joinedDate}.\n'\
			 							'Your rank should be {currentRank}!\n'\
			 							'{rankMsg}'.format(name=dbusername,days=numDays, joinedDate=niceJoinedDate, currentRank=rank, rankMsg=rankMsg))
			conn.close()

		except Exception as e:
			await message.channel.send('Username or discordID not found. Please enter the name when you applied. \n' \
										'You may use "$contains partOfUsername" to search a part of your name. \n' \
										'You may use "$setID username" to set your discord ID.')
			print(e)
		

	if message.content.startswith('$contains'):
		username = message.content[10:]
		conn = db.connect()
		result = conn.execute("SELECT username FROM members WHERE username ilike '%%{username}%%'".format(username=username)).fetchall()
		users = sorted([user[0] for user in result],key=str.casefold)

		if len(users)>0:
			await message.channel.send('Here is a list of names that contain {username}: \n'.format(username=username))
			userString = '\n'.join(users)
			await message.channel.send(userString)
		else:
			await message.channel.send('No users contained string {username}.'.format(username=username))
		conn.close()


	if message.content.startswith('$setID'):
		username = message.content[7:]
		discordID = message.author.id
		conn = db.connect()
		if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{username}'))".format(username=username)).fetchone()[0] == True:
			result = conn.execute("UPDATE members SET discordID={discordID} WHERE LOWER(username) = LOWER('{username}')".format(discordID=discordID,username=username))
			await message.channel.send('Your ID has been successfully assigned to {username}.'.format(username=username))
		else:
			await message.channel.send('Username not found. Please enter the name when you applied. \n' \
										'You may also use $contains to search a part of your name \n')
		conn.close()

	if message.content.startswith('$assignID'):
		msg = message.content[10:]
		if any(role.id in reqRoles for role in message.author.roles):

			result = [x.strip() for x in msg.split(',')]

			username = result[0]
			discordID = result[1]

			conn = db.connect()
			if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{username}'))".format(username=username)).fetchone()[0] == True:
				result = conn.execute("UPDATE members SET discordID={discordID} WHERE LOWER(username) = LOWER('{username}')".format(discordID=discordID,username=username))
				await message.channel.send('ID {discordID} has been successfully assigned to {username}.'.format(discordID=discordID,username=username))
			else:
				await message.channel.send('Username not found. Please enter the name when you applied. \n' \
										'You may also use $contains to search a part of your name \n')
			conn.close()
		else:
			await message.channel.send('You don\'t have the required role!')

	



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



	if message.content.startswith('$total'):
		conn = db.connect()
		totalMembers = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
		await message.channel.send('There are a total of {0} Noble Members.'.format(totalMembers))
		conn.close()



	if message.content.startswith('$new'):
		if any(role.id in reqRoles for role in message.author.roles):
			userToAdd = message.content[5:]
			date = datetime.now().date()
			conn = db.connect()
			if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{user}'))".format(user=userToAdd)).fetchone()[0] == True:
				await message.channel.send('{user} was not added and already exists!'.format(user=userToAdd))
			else:
				conn.execute("INSERT INTO members(username,joined) VALUES('{user}','{date}')".format(user=userToAdd,date=date))
				await message.channel.send('{user} has been successfully added to the clan sheet!'.format(user=userToAdd))
			conn.close()
		else:
			await message.channel.send('You don\'t have the required role!')



	if message.content.startswith('$remove'):
		if any(role.id in reqRoles for role in message.author.roles):
			userToRemove = message.content[8:]
			date = datetime.now().date()
			conn = db.connect()
			if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{user}'))".format(user=userToRemove)).fetchone()[0] == False:
				await message.channel.send('{user} was not found!'.format(user=userToRemove))
			else:
				conn.execute("DELETE FROM members WHERE lower(username) = LOWER('{user}')".format(user=userToRemove))
				await message.channel.send('{user} has been successfully removed from the clan sheet!'.format(user=userToRemove))
			conn.close()
		else:
			await message.channel.send('You don\'t have the required role!')
	


	if message.content.startswith('$clansheet'):
		if any(role.id in reqRoles for role in message.author.roles):
			await message.channel.send(clansheet)
		else:
			await message.channel.send('You don\'t have the required role!')



	if message.content.startswith('$updatefund'):
		msg = message.content[12:]
		msgContent = [x.strip() for x in msg.split(',')]

		if len(msgContent) != 2:
			await message.channel.send('Error: You need to add 2 fields separated with 1 comma.'\
				' For example: $updatefund name,amount')
			return

		if any(role.id in reqRoles for role in message.author.roles):
			conn = db.connect()
			date = datetime.now().date()
			username = msgContent[0].lower()
			amt = int(msgContent[1].replace(',', ''))

			#They don't already exist in the table so add them and the value
			if conn.execute("SELECT EXISTS(SELECT 1 FROM clanfund WHERE LOWER(username) = LOWER('{username}'))".format(username=username)).fetchone()[0] == False:
				conn.execute("INSERT INTO clanfund(username, amount, last_updated) VALUES('{username}', {amt}, '{date}') ".format(username=username, amt=amt,date=date))
				await message.channel.send('{username} was successfully added to the clanfund database.'.format(username=username))
			else:
				#since the user will enter -# for removing, we can just use + here
				conn.execute("UPDATE clanfund SET amount=amount+{amt} WHERE username='{username}'".format(amt=amt, username=username))
			conn.close()

			if amt <0:
				await message.channel.send('You removed {:,d} GP from the clan fund!'.format(abs(amt)))
			elif amt>0:
				await message.channel.send('You added {:,d} GP to the clan fund!'.format(amt))
			else:
				await message.channel.send('You didn\'t do anything to the clan fund! Go make some GP!')

		else:
			await message.channel.send('You don\'t have the required role!')
			

	if message.content.startswith('$detailfund'):
		if any(role.id in reqRoles for role in message.author.roles):
			conn = db.connect()
			fund = conn.execute("SELECT * FROM clanfund WHERE amount != 0").fetchall()
			conn.close()
			[await message.channel.send("As of {date}, {username} has {amt:,} GP.".format(date=x[2].strftime('%b %d, %Y'), username=x[0], amt=x[1])) for x in fund]
			await message.channel.send('There is a total of {amt:,} GP in the clan fund!'.format(amt=sum([x[1] for x in fund])))
		else:
			await message.channel.send('You don\'t have the required role!')


	if message.content.startswith('$clanfund'):
		conn = db.connect()
		gp = conn.execute("SELECT SUM(amount) FROM clanfund").fetchone()
		conn.close()
		await message.channel.send('There is a total of {gp:,} GP in the clan fund!'.format(gp=gp[0]))

	
	if message.content.startswith('$help'):
			await message.channel.send("I currently know the following commands:\n"\
				"1. $total - how many members we have.\n"
				"2. $setID username - sets your unique discord ID in the database.\n"\
				"3. $length - checks how long you have been a member (only if ID is set).\n"\
				"4. $length username - checks how long the user has been a member.\n"\
				"5. $contains partOfUsername - assists with finding a username you may have fully forgetten.\n"\
				"6. $updatename old,new - updates your username on our tracker.\n"\
				"7. $clanfund - checks how much GP is in the clan fund.\n"\
				"\nFor any additional help or suggestions, please message Noble Gaels.")
				
			if any(role.id in reqRoles for role in message.author.roles):
				await message.channel.send("I currently know the following admin commands:\n"\
				"8. $new username - adds a new user to the spreadsheet.\n"\
				"9. $updatefund user,amt - adds or removes funds. To remove, use negative amt.\n")

client.run(TOKEN)
db.dispose()