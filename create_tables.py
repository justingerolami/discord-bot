from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

# Heroku database url


# This function creates the "members" table in the database
# It also populates the database with previous data from the clan csv
def setup_members_table(url,clansheetData=None):
	engine = create_engine(url, echo = False,poolclass=NullPool)
	engine.execute("CREATE TABLE IF NOT EXISTS members (username text PRIMARY KEY, joined timestamp)")
	
	if clansheetData not None:
		clansheetData.to_sql('members', con = engine, if_exists='append',index=False)
	
	engine.dispose()


def setup_clanfund_table(url):
	engine = create_engine(url, echo = False, poolclass=NullPool)
	engine.execute("CREATE TABLE IF NOT EXISTS clanfund (username text PRIMARY KEY, amount int, last_updated timestamp)")
	engine.dispose()


# This function loads the previous data from the csv into a dataframe
# Returns a dataframe
def import_clansheet(filename):
	clanData = pd.read_csv(filename)
	date = clanData["joined"]

	# Remove the time component from the old spreadsheet
	clanData["joined"] = pd.to_datetime(date, format='%m/%d/%Y %H:%M:%S').dt.date
	return clanData



def main():
	filename = "clansheet.csv"
	url = os.getenv('url')
	clansheet = os.getenv('clansheet')

	clansheetData = import_clansheet(filename)
	setup_members_table(url,clansheetData)

	setup_clanfund_table(url)


if __name__ == '__main__':
	main()
