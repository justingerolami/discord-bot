
'''
This function calculates which rank the user should have, based on the number of days
since the joined. 

Takes a days parameter pulled from the database and bases a month off 30 days.
'''
def calculate_rank(days):
	month=30
	if days <14:
		rank ='new recruit bronze'
		daysUntilRank = 14-days
	elif days >= 14 and days<month*2: #day is between 14 and 30
		rank = 'bronze'
		daysUntilRank = month*2 - days
	elif days >=month*2 and days<month*4: #1-2 months
		rank = 'iron'
		daysUntilRank = month*4 - days
	elif days >=month*4 and days<month*6: #2-4 months
		rank = 'steel'
		daysUntilRank = month*6 - days
	elif days >=month*6 and days<month*8: #4-6 months
		rank = 'gold'
		daysUntilRank = month*8 - days
	elif days >=month*8 and days<month*12: #6-8 months
		rank = 'mith'
		daysUntilRank = month*12 - days
	elif days >=month*12 and days<month*18: #8-12 months
		rank='addy'
		daysUntilRank = month*18 - days
	elif days >=month*18 and days<month*24: #12-18 months
		rank = 'rune'
		daysUntilRank = month*24 - days
	elif days >=month*24: 
		rank = 'dragon'
		daysUntilRank = -1
	else:
		rank = 'Error: Report this to Gaels'
		daysUntilRank = -1

	return rank, daysUntilRank