# Scrapes injury data from http://www.prosportstransactions.com
# Collects all missed games due to  injury from Oct 10, 2012 to Aug 12, 2020

import requests
import pandas as pd
from bs4 import BeautifulSoup


def clear_bullet(s):
    return s.replace('• ', '')


nba_injuries = pd.DataFrame(columns=['Date', 'Team', 'Player', 'Injury'])

# Scrape injury data from site
for page in range(366):
    URL = 'http://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate=2012-10-30&EndDate=2020-08-12&InjuriesChkBx=yes&Submit=Search&start=' + str(25 * page)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    results = soup.find_all('tr', align='left')
    
    for result in results:
        entry = result.text.strip().split('\n')
        nba_injuries = nba_injuries.append({'Date': entry[0], 'Team': entry[1], 'Player': entry[3], 'Injury': entry[4]}, ignore_index=True)
        
        
# Data cleaning
# Remove all entries without player name (i.e. returned to lineup)        

nba_injuries = nba_injuries[nba_injuries.Player != ' ']
nba_injuries['Player'] = nba_injuries['Player'].apply(clear_bullet)


# Save as csv
nba_injuries.to_csv('injuries.csv', index=False)