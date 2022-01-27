from asynchat import async_chat
import os
import discord
from discord.ext.commands import Bot
from discord.ext import tasks
from discord.utils import get
from discord.ui import Button, View
import member_functions as mf
from sqlalchemy import create_engine
from datetime import datetime
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

#Github
TOKEN = os.environ['TOKEN']
url = os.environ['URL']
clansheet = os.environ['CLANSHEET']

NOBLES = int(os.getenv('NOBLES'))
MODS = int(os.getenv('MODERATORS'))
ADMIN = int(os.getenv('ADMIN'))
NEWMEMBER = int(os.getenv('NEWMEMBER'))


reqRoles = [NOBLES,MODS,ADMIN]

client=Bot(command_prefix="$")

#client = discord.Client()
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
		" please fill out the clan app by clicking the button here: <#936082496989315134>."\
		" Please change your server nickname to match your rsn by clicking the arrow beside"\
		" noble bros 2.0' -> 'change nickname'."\
		" If you have any questions, please message one of the admins listed under 'member list'.").format(member_name=member.mention))


@client.event
async def on_message(message):
	

	if message.author == client.user:
		return

	if message.content.startswith('$length'):
		if len(message.content) == 7:
			username = ''
			discordID = message.author.id
		else:
			username = message.content[8:]
			discordID = -1

	
		#hack because admin may look up by someone else's ID
		if username == message.author.id:
			discordID = username

		try:
			#connect to the database
			conn = db.connect()

			#query for the joined date and the age of the user
			result = conn.execute("SELECT username,joined, AGE(joined) FROM members WHERE LOWER(username) = LOWER('{username}') OR discordID = '{username}' OR discordID = '{discordID}'".format(username=username, discordID=discordID)).fetchone()

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
			result = conn.execute("UPDATE members SET discordID='{discordID}' WHERE LOWER(username) = LOWER('{username}')".format(discordID=discordID,username=username))
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
				result = conn.execute("UPDATE members SET discordID='{discordID}' WHERE LOWER(username) = LOWER('{username}')".format(discordID=discordID,username=username))
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
				"8. $new username - adds a new user to the database.\n"\
				"9. $remove username - remove a user from the database\n"\
				"10. $assignID username,id - sets a users discord ID\n"\
				"11. $updatefund user,amt - adds or removes funds. To remove, use negative amt.\n")
	await client.process_commands(message)


@tasks.loop(hours=1)
async def apply_button(ctx):
	hoursToSeconds = 1*60*60
	
	submit_channel = client.get_channel(739285627190640780)

	new_member_button = Button(label="New Member Application", style=discord.ButtonStyle.primary)
	old_member_button = Button(label="Previous Member Application", style=discord.ButtonStyle.green)
       
	async def new_member_callback(interaction):
		q_list = [
			'What is your RSN?',
			'What is your combat level?',
			'What is your total level?',
			'What is your favorite thing to do in OSRS?',
			'How did you hear about us?',
			'Are you listed on any ban lists (WDR, Runewatch, Sythe, etc)?',
			'Have you read the <#638098870378823694> page? **If you do not follow instructions ' \
			'on that page, your application will be auto-denied.**']
		a_list = []
		await interaction.response.defer()
		#await interaction.response.send_message(interaction.user.id)
		channel = await interaction.user.create_dm()

		def check(m):
			return m.content is not None and m.channel == channel and m.author.id== interaction.user.id

		for question in q_list:
			await channel.send(question)
			msg = await client.wait_for('message', check=check)
			a_list.append(msg.content)

		userToAdd = a_list[0]
		date = datetime.now().date()
		discordID = interaction.user.id

		submit_wait = True
		while submit_wait:
			await channel.send('End of questions - type "submit" to finish or "quit" to cancel.')
			msg = await client.wait_for('message', check=check)
			if "submit" in msg.content.lower():
				submit_wait = False
				answers = "\n".join(f'{a}. {b}' for a, b in enumerate(a_list, 1))
				if "noblebros" in answers.lower() or "noble bros" in answers.lower():
					conn = db.connect()
					if (conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{user}'))".format(user=userToAdd)).fetchone()[0] == False) and (conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE discordID = '{discordID}')".format(discordID=discordID)).fetchone()[0] == False):
						conn.execute("INSERT INTO members(username,joined,discordID) VALUES('{user}','{date}', '{discordID}')".format(user=userToAdd,date=date, discordID=discordID))
					else:
						await channel.send('Welcome back to Noble Bros! You are already in our database. \n'\
											'Please use the Previous Member Application instead.')
						break

					await channel.send("Thank you for completing the application. You have been accepted and assigned your role! \n"\
										"Please wait for an admin to add you in game.")

					role = interaction.guild.get_role(NEWMEMBER)
					await interaction.user.add_roles(role)

					embed=discord.Embed(title="**Application for Noble Bros: " + userToAdd+"**", description="This is the application for NobleBros sent by " + userToAdd, color=0x04ff00)
					embed.add_field(name="**RSN?**", value=a_list[0], inline=True)
					embed.add_field(name="**DISCORD ID?**", value=discordID, inline=True)
					embed.add_field(name="**COMBAT LVL?**", value=a_list[1], inline=False)
					embed.add_field(name="**TOTAL LVL?**", value=a_list[2], inline=True)
					embed.add_field(name="**THEIR FAVORITE THING TO DO ON OSRS?**", value=a_list[3], inline=False)
					embed.add_field(name="**HOW THEY HEARD ABOUT US?**", value=a_list[4], inline=False)
					embed.add_field(name="**ARE THEY ON ANY BANLISTS (VERIFY MANUALLY)?**", value=a_list[5], inline=False)
					embed.add_field(name="**DID THEY READ THE RULES?**", value=a_list[6], inline=False)
					await submit_channel.send(embed=embed)

				else:
					await channel.send("You did not follow the instructions in <#638098870378823694>. \n"\
										"Please review the rules and reapply.")
					
					embed=discord.Embed(title="**Application for Noble Bros: " + userToAdd+"**", description="This is the application for NobleBros sent by " + userToAdd, color=0xff0000)
					embed.add_field(name="**RSN?**", value=a_list[0], inline=True)
					embed.add_field(name="**DISCORD ID?**", value=discordID, inline=True)
					embed.add_field(name="**COMBAT LVL?**", value=a_list[1], inline=False)
					embed.add_field(name="**TOTAL LVL?**", value=a_list[2], inline=True)
					embed.add_field(name="**THEIR FAVORITE THING TO DO ON OSRS?**", value=a_list[3], inline=False)
					embed.add_field(name="**HOW THEY HEARD ABOUT US?**", value=a_list[4], inline=False)
					embed.add_field(name="**ARE THEY ON ANY BANLISTS (VERIFY MANUALLY)?**", value=a_list[5], inline=False)
					embed.add_field(name="**DID THEY READ THE RULES?**", value=a_list[6], inline=False)
					await submit_channel.send(embed=embed)
			elif 'quit' in msg.content.lower():
				await channel.send("Please feel free to apply again when you're ready!")
				break


	async def old_member_callback(interaction):
		a_list = []
		q_list = [
			'What is the username we have on file?',
			'What is your current username?']

		await interaction.response.defer()
		#await interaction.response.send_message(interaction.user.id)
		channel = await interaction.user.create_dm()

		def check(m):
			return m.content is not None and m.channel == channel and m.author.id== interaction.user.id

		discordID = interaction.user.id
		conn = db.connect()
		successfulRejoin = False

		if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE discordID = '{discordID}')".format(discordID=discordID)).fetchone()[0] == True:
			await channel.send('Welcome back to Noble Bros! I\'ve found you in our database.')
			result = conn.execute("SELECT username FROM members WHERE discordID = '{discordID}'".format(discordID=discordID)).fetchone()
			dbusername = result[0]
			a_list.append(dbusername)
			await channel.send(q_list[1])
			msg = await client.wait_for('message', check=check)
			a_list.append(msg.content)
			userToAdd = a_list[1]

			conn.execute("UPDATE members SET username='{username}' WHERE discordID = '{discordID}' and LOWER(username) = LOWER('{oldUsername}')".format(discordID=discordID,username=userToAdd, oldUsername=dbusername))
			successfulRejoin=True

			
		else:
			for question in q_list:
				await channel.send(question)
				msg = await client.wait_for('message', check=check)
				a_list.append(msg.content)

			dbusername = a_list[0]
			userToAdd = a_list[1]
			
			if conn.execute("SELECT EXISTS(SELECT 1 FROM members WHERE LOWER(username) = LOWER('{user}'))".format(user=dbusername)).fetchone()[0] == True:
				conn.execute("UPDATE members SET discordID='{discordID}',username='{newUsername}' WHERE LOWER(username) = LOWER('{oldUsername}')".format(discordID=discordID,newUsername=userToAdd,oldUsername=dbusername))
				successfulRejoin=True

			else:
				await channel.send("That username is not in our system.\n"\
									"Please reapply with the username we have on file or apply as a new member.")
		
		if successfulRejoin == True:
			await channel.send("You have been accepted and assigned your role! \n"\
									"Please wait for an admin to add you in game.")

			role = interaction.guild.get_role(NEWMEMBER)
			await interaction.user.add_roles(role)

			embed=discord.Embed(title="**Rejoin Application for Noble Bros: " + userToAdd+"**", description="This is the application for NobleBros sent by " + userToAdd, color=0x04ff00)
			embed.add_field(name="**OLD RSN?**", value=a_list[0], inline=True)
			embed.add_field(name="**NEW RSN?**", value=a_list[1], inline=True)
			embed.add_field(name="**DISCORD ID?**", value=discordID, inline=True)
			await submit_channel.send(embed=embed)
					

	new_member_button.callback = new_member_callback
	old_member_button.callback = old_member_callback
	app_view = View()
	app_view.add_item(new_member_button)
	app_view.add_item(old_member_button)
	await ctx.send("Press the button to apply after you have read the rules in <#638098870378823694>",view=app_view, delete_after=hoursToSeconds)

@client.command()
async def start_application(ctx):
	await ctx.send(apply_button.start(ctx))

client.run(TOKEN)

db.dispose()