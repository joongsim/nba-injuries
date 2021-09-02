# Scrapes injury data from http://www.prosportstransactions.com
# Collects all missed games due to  injury from Oct 10, 2012 to Aug 12, 2020

import requests
import pandas as pd
import nba_api.stats.static.players as players

from bs4 import BeautifulSoup
from nba_api.stats import endpoints


def split_injured_players(players_list):
    split_players_list = []
    for player in players_list:
        split_player = player.split(' / ')
        for item in split_player:
            split_players_list.append(item)

    return split_players_list

def match_official_name(df, split_name_dict):
    '''
    Returns variation of name matching the official records
    If no match is found, NA
    '''
    splits = df.Player.str.split(' / ')
    official_names = []
    print(type(splits))
    for names in splits:
        match_flag = 0
        for name in names:
            if name in split_name_dict.values():
                official_names.append(name)
                match_flag = 1
            
        if match_flag < 1:
            official_names.append('NA')

    return official_names


if __name__ == '__main__':
    nba_injuries = pd.DataFrame(columns=['Date', 'Team', 'Player', 'Injury'])

    # Scrape injury data from site
    for n in range(366):
        URL = 'http://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate=2012-10-30&EndDate=2020-08-12&InjuriesChkBx=yes&Submit=Search&start=' + str(25 * n)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        print('Page ' + str(n) + '...', end='\r')
        results = soup.find_all('tr', align='left')
        
        for result in results:
            entry = result.text.strip().split('\n')
            nba_injuries = nba_injuries.append({'Date': entry[0], 'Team': entry[1], 'Player': entry[3], 'Injury': entry[4]}, ignore_index=True)
            
            
    # Data cleaning
    # Remove all entries without player name (i.e. returned to lineup)        

    nba_injuries = nba_injuries[nba_injuries.Player != ' ']
    nba_injuries['Player'] = nba_injuries['Player'].str.replace('• ', '', regex=False) \
        .str.replace('.', '', regex=False)

    # Retrieve official player list - need to get id's to fetch player/game info
    players_df = pd.DataFrame(players.get_players())
    players_df.full_name = players_df.full_name.str.replace('.', '', regex=False)

    # Match injured players to official NBA entries
    # Many players are listed with multiple names/aliases in the injuries database
    # These are separated by a slash ('/') - need to find out which one of them matches
    # the official record
    mult_names = nba_injuries[nba_injuries['Player'].str.contains('/')].copy()
    one_name = nba_injuries[~nba_injuries['Player'].str.contains('/')]

    player_names_dict = players_df['full_name'].to_dict()
    official_names = match_official_name(mult_names, player_names_dict)
    mult_names['official'] = official_names

    # Drop unmatched entries and replace the original names with official matches
    mult_names = mult_names.dropna() \
        .drop(columns=['Player']) \
        .rename(columns={'official':'Player'})

    # Concatenate the one_name and mult_names dfs
    injuries_official_names = pd.concat([one_name, mult_names])

    # Merge injuries df with player ids
    merged_df = injuries_official_names.merge(players_df[['full_name', 'id']], 
        how='left', left_on='Player', right_on='full_name') \
        .dropna()

    # Convert ids to string and drop the decimal place
    merged_df.id = merged_df.id.apply(str) \
        .str[:-2]
    


    # Save as csv
    merged_df.to_csv('merged_injuries.csv', index=False)
