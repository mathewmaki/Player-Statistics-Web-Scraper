# Player Statistics Web Scraper
# Created by Mathew Maki 
# Created 2020, Updated 2021
import sys, re, os.path, selenium, urllib.request, csv
from bs4 import BeautifulSoup
from selenium import webdriver


class WebScraper():

	def __init__(self, url, path):
		'''
		Initializes chromedriver with a url.

		Input:
			url (str) - the url of the website to scrape
			path (str) - the path for chrome driver
		Returns: 
		    None
		'''
		# Set url, and the Chrome driver path
		self.url = url
		self.path = path

		# Initialize Chrome Webdriver
		self.driver = webdriver.Chrome(self.path)

	def getWebData(self):
		'''
		Gets and parses all the HTML data from the website and returns it.

		Input:
			None
		Returns: 
		    None
		'''
		# Create a dictionary to hold the HTML data
		self.html_data = {}

		# Create a list for the HTML class names of the desired data
		self.data_category = ['name', 'position', 'jersey_number', 'rank', 'games_played', 'goals', 'penalty_minutes']
		player_link = []
		html_template = '{} ng-binding ng-scope'

		# Get the HTML data from the website and close Chrome Webdriver
		self.driver.get(self.url)
		res = self.driver.execute_script('return document.documentElement.outerHTML')
		self.driver.quit()

		# Initialize BeautifulSoup to parse the HTML data 
		self.soup = BeautifulSoup(res, 'html.parser')

		# Get the HTML data from each of the td tags and save it in the HTML data dictonary
		# with the HTML class as the key 
		for category in self.data_category:
			self.html_data[category] = self.soup.find_all('td', {'class': html_template.format(category)})

		# Get the URL's for each player's page and add it to the HTML data dictionary
		self.data_category.append('player_link')
		for links in self.html_data['name']:
			section = links.find('a')
			link = section.get('href')
			player_link.append(link)
		self.html_data['player_link'] = player_link

	def setPlayerDB(self):
		'''
		Creates a database of player players.

		Input:
			None
		Returns: 
		    None
		'''
		# Create a dictionary to hold each player object
		self.players = {}

		# Loop through every player on the team and create a unique player object 
		# for each player
		for i in range(len(self.html_data['name'])):
			player_info = []
			for category in self.data_category:
				player_info.append(self.html_data[category][i])
			player = Player(player_info.pop(0))
			name = player.getName()
			player.setData(*player_info)

			# Add the player object to the player dictionary with the player's name
			# as the key
			self.players[name] = player


	def createFile(self):
		'''
		Creates a csv file containing all of the player info.

		Input:
			None
		Returns: 
		    self.team_data (dict) - dictionary containing all the team data
		'''
		# Create a list for the data headers, and dictionary for the data of each player on the team
		data_header = ['Name', 'Number', 'Ranking', 'Position', 'Games Played', 'Goals', 'Pentalty Mins', 'Photo']
		self.team_data = {'Name': [], 'Number': [], 'Ranking': [], 'Position': [], 'Games Played': [], 'Goals': [], 'Pentalty Mins': [], 'Photo': []}

		# Get the data for each player and add it to the team data dictionary
		for info in self.players.values():
			data = info.getData()
			index = 0
			for val in self.team_data.values():
				val.append(data[index])
				index += 1

		# Create a csv file and write all the player data to it
		player_file = open('PlayerStats.csv', 'w')
		writer = csv.writer(player_file)
		writer.writerow(data_header)
		for i in range(len(self.team_data['Name'])):
			row = []
			for info in self.team_data.values():
				row.append(info[i])
			writer.writerow(row)
		player_file.close()

		return self.team_data

class Player():

	def __init__(self, name):
		'''
		Initializes a player object.

		Input:
			name (str) - the name of the player
		Returns: 
		    None
		'''
		player_name = name.get_text('a')
		player_name = player_name.replace('(total)a a+', '')
		self.name = player_name

	def setData(self, pos, number, rank, games, goals, penalty, link):
		'''
		Sets all of the data for the player object.

		Input:
			pos (str) - html data for the player position
			number (str) - html data for the player's number
			rank (str) - html data for the player's rank
			games (str) - html data for the number of games the player has played
			goals (str) - html data for the number of goals the player has
			pentalty (str) - html data for the number of penalty minutes the player has
			link (str) - the link for the player's picture
		Returns:
			None
		'''
		self.setPos(pos)
		self.setNumber(number)
		self.setRank(rank)
		self.setGamesPlayed(games)
		self.setGoals(goals)
		self.setPenaltyMins(penalty)
		self.setLink(link)

	def getData(self):
		'''
		Returns all of the data for the player object in a list.

		Input:
			None
		Returns: 
		    data (list) - a list containing all of the data for the player
		'''
		data = []
		data.append(self.getName())
		data.append(self.getNumber())
		data.append(self.getRank())
		data.append(self.getPos())
		data.append(self.getGamesPlayed())
		data.append(self.getGoals())
		data.append(self.getPenaltyMins())
		data.append(self.getLink())
		return data

	def getPicture(self, data):
		'''
		Gets and retrieves the player picture and returns the filepath of the saved image.

		Input:
			data (str) - the player link
		Returns: 
		    filepath (str) - the filepath to the retrived player picture
		'''
		# Set the defult picture URL and filepath
		defult_url = 'http://assets.leaguestat.com/sjhl/logos/16.jpg'
		save_path = 'player_photos/'

		# Link match regex and set the URL to be tested
		link_match = re.findall(r'\d{4}', data)
		test_url = 'http://assets.leaguestat.com/sjhl/240x240/' + str(link_match)[2:-2] + '.jpg'

		# Name match regex and setup the picture name and filepath
		name_match = re.findall(r'\w+(?:-)\w+', data)
		pic_name = str(name_match).replace('', '')[2:-2]
		filepath = save_path + pic_name + '.jpg'

		# Try and save the picture using the test URL and use the defult image if the
		# test URL fails
		try:
			result = urllib.request.Request(test_url)
			urllib.request.urlretrieve(test_url, filepath)
		except urllib.error.HTTPError as error:
			if error.code == 404:
				print('{} picture not found. Using defult image.'.format(pic_name))
				urllib.request.urlretrieve(defult_url, filepath)
		finally:
			return filepath

	def setPos(self, data):
		'''
		Sets the position of the player.

		Input:
			data (str) - html data for the player position
		Returns:
			None
		'''
		self.pos = data.get_text('span')
		if self.pos == '':
			self.pos = 'N/A'

	def setNumber(self, data):
		'''
		Sets the number of the player.

		Input:
			data (str) - html data for the player's number
		Returns:
			None
		'''
		self.number = data.get_text('span')
		if self.number == '':
			self.number = 'N/A'

	def setRank(self, data):
		'''
		Sets the rank of the player.

		Input:
			data (str) - html data for the player's rank
		Returns:
			None
		'''
		self.rank = data.get_text('span')
		if self.rank == '':
			self.rank = 'N/A'

	def setGamesPlayed(self, data):
		'''
		Sets the number of games of the player.

		Input:
			data (str) - html data for the number of games the player has played
		Returns:
			None
		'''
		self.games_played = data.get_text('span')

	def setGoals(self, data):
		'''
		Sets the number of goals the player has.

		Input:
			data (str) - html data for the number of goals the player has
		Returns:
			None
		'''
		self.goals = data.get_text('span')

	def setPenaltyMins(self, data):
		'''
		Sets the number of penaly minutes the player has.

		Input:
			data (str) - html data for the player's penalty minutes
		Returns:
			None
		'''
		self.penalty_mins = data.get_text('span')

	def setLink(self, link):
		'''
		Sets the link for the player's picture.

		Input:
			link (str) - the link to the player's picture
		Returns:
			None
		'''
		self.link = self.getPicture(link)

	def getName(self):
		'''
		Returns the name of the player.

		Input:
			None
		Returns:
			self.name (str) - the name of the player
		'''
		return self.name

	def getNumber(self):
		'''
		Returns the number of the player.

		Input:
			None
		Returns:
			self.number (str) - the number of the player
		'''
		return self.number

	def getRank(self):
		'''
		Returns the rank of the player.

		Input:
			None
		Returns:
			self.rank (str) - the rank of the player
		'''
		return self.rank

	def getPos(self):
		'''
		Returns the position of the player.

		Input:
			None
		Returns:
			self.pos (str) - the position of the player
		'''
		return self.pos

	def getGamesPlayed(self):
		'''
		Returns the number of games the player has played.

		Input:
			None
		Returns:
			self.games_played (str) - the number of games the player has played
		'''
		return self.games_played

	def getGoals(self):
		'''
		Returns the number of goals the player has.

		Input:
			None
		Returns:
			self.goals (str) - the number of goals the player has
		'''
		return self.goals

	def getPenaltyMins(self):
		'''
		Returns the number of penalty minutes the player has.

		Input:
			None
		Returns:
			self.penalty_mins (str) - the number of penalty minutes the player has
		'''
		return self.penalty_mins

	def getLink(self):
		'''
		Returns the filepath of the player's picture.

		Input:
			None
		Returns:
			self.link (str) - the filepath of the player's picture
		'''
		return self.link

if __name__ == '__main__':

	# Set the URL and path for the Chrome driver
	url = 'https://www.humboldtbroncos.com/stats/player-stats/16/41?playertype=skater&position=skaters&rookie=no&sort=points&statstype=standard&page=1&league=3'
	path = 'paste chromedriver path here'

	# Try getting the data 10 times in case page loads incorrectly
	success = False
	counter = 0
	while not success and counter < 10:
		scraper = WebScraper(url, path)
		scraper.getWebData()
		scraper.setPlayerDB()
		team_DB = scraper.createFile()
		if len(team_DB['Name']) != 0:
			success = True
		else:
			print('Error getting data. Trying again...')
			counter += 1
	if success:
		print('Finished!')
	else:
		print('Could not retrive data.')
