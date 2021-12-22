import argparse
import numpy as np
import pandas as pd
import sqlite3 as sql
import urllib

from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import CommonPlayerInfo, PlayerGameLog


def get_proxies():
    return [str(proxy).split('\\')[0][2:] for proxy in urllib.request.urlopen("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=1000&country=all&ssl=yes&anonymity=all&simplified=true").readlines()]

def update_players(conn):
    '''
    Get list of all players from nba-api and store as table
    '''
    df_players = pd.DataFrame(players.get_players()).astype({'id': 'str'})
    
    try:
        df_players.to_sql('Player', conn, index=False)
    except:
        pass

def get_recent_players(conn):
    # Gets ids of players who were active after 2011
    player_ids = pd.read_sql('SELECT PERSON_ID FROM player_attributes WHERE TO_YEAR > 2011', conn)['PERSON_ID'].values
    return player_ids

def height_to_inches(ht):
    '''
    Converts player height to inches. Takes series of str as input and returns int.
    '''
    ht_split = ht.str.split('-')
    try:
        ht_inches = int(ht_split[0][0]) * 12 + int(ht_split[0][1])
        return ht_inches
    except ValueError:
        return 'NA'

def last_7_days(df, index_col):
    try:
        df = df.set_index(index_col).sort_index()
    except KeyError as err:
        print('Error: ', err)
        print('index_col {} most likely does not exist in DataFrame, or is not in datetime format'.format(index_col))
    else:
        df['last_7_days'] = df.groupby('Player_ID')['AST'] \
                                    .transform(lambda x: x.rolling(pd.to_timedelta(7, 'days')).count() - 1)

        df = df.reset_index()

        return df

def update_player_attributes(conn, proxies):
    player_attribute_dfs = []
    player_ids = pd.read_sql('SELECT id FROM Player', conn)['id'].values
    player_attribute_dfs = [get_common_player_info(player_id=player_id, proxies=proxies) for player_id in player_ids]
    player_attribute_df = pd.concat(player_attribute_dfs)

    player_attribute_df.to_sql('Player_Attributes', conn, index=False, if_exists='replace')



def get_common_player_info(player_id, proxies):
    '''
    Get common player info from nba-api and store as table
    '''

    no_res = True
    proxy_collection_counter = 0
    proxy_index = 0

    while no_res:
        # call without proxy
        try:
            res = CommonPlayerInfo(player_id=player_id, timeout=3).get_data_frames()
            no_res = False
            print(player_id)
            break
        except:
            # if that fails
            while no_res:
                # try getting with the first proxy
                try: 
                    proxy="http://" + proxies[proxy_index]
                    res = CommonPlayerInfo(player_id=player_id, proxy=proxy, timeout=3).get_data_frames()
                    print(player_id, proxy)
                    no_res = False
                    break
                except:
                    # if that fails, move on to next proxy unless out of proxies
                    if (proxy_index + 1) >= len(proxies):
                        # unless tried proxies 5 times
                        if proxy_collection_counter < 6:
                            # if out of proxies: get more proxies, fix counters, and try without a proxy again
                            proxy_index = 0
                            proxy_collection_counter = proxy_collection_counter + 1
                            print(player_id, ' failed {} times'.format(proxy_collection_counter))
                            proxies = get_proxies()
                            break
                        else:
                            return None
                    else:
                        proxy_index = proxy_index + 1
                        
    # merge the common player info and player headline stats and drop timeframe                   
    res_df = pd.merge(res[0], res[1], how='left', left_on=['PERSON_ID', 'DISPLAY_FIRST_LAST'], right_on=['PLAYER_ID', 'PLAYER_NAME'])
    res_df = res_df.drop(['TimeFrame'], axis=1)

    # convert HEIGHT to inches
    res_df.HEIGHT = height_to_inches(res_df.HEIGHT)

    return res_df

def update_gamelogs(conn, proxies, seasons, hist=False):
    player_gamelog_dfs = []
    print(hist)

    if hist:
        # Fetch players who were active during 2012-2020
        player_ids = get_recent_players(conn)
    else:
        # Fetch all currently active players
        player_ids = [player['id'] for player in players.get_active_players()]
        

    player_gamelog_dfs = [get_player_gamelogs(player_id=player_id, season=season, proxies=proxies) for player_id in player_ids for season in seasons]

    player_gamelog_df = pd.concat(player_gamelog_dfs)

    # Convert GAME_DATE col to datetime
    player_gamelog_df.GAME_DATE = pd.to_datetime(player_gamelog_df.GAME_DATE)

    # NEW COLUMN: games in last 7 days
    player_gamelog_df = last_7_days(player_gamelog_df, 'GAME_DATE')

    if hist:
        player_gamelog_df.to_sql('Player_Gamelogs', conn, index=False, if_exists='replace')
    else:
        # Create temp table to store current season gamelogs
        # Insert temp table into main table, ignoring duplicates
        player_gamelog_df.to_sql('temp', conn, index=False, if_exists='replace')
        cur = conn.cursor()
        sql = '''INSERT INTO Player_Gamelogs 
                        SELECT * 
                        FROM temp t 
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM Player_Gamelogs p
                            WHERE p.Player_ID = t.Player_ID
                                AND p.Game_ID = t.Game_ID)'''
        cur.execute(sql)
        conn.commit()






def get_player_gamelogs(player_id, season, proxies):
    '''
    Get common player info from nba-api and store as table
    '''

    no_res = True
    proxy_collection_counter = 0
    proxy_index = 0

    while no_res:
        # try getting a response without a proxy
        try:
            res = PlayerGameLog(player_id=player_id, season=season, timeout=3).get_data_frames()[0]
            no_res = False
            print(player_id, season)
            break
        except:
            # if that fails
            while no_res:
                # try getting with a certain proxy
                try: 
                    proxy="http://" + proxies[proxy_index]
                    res = PlayerGameLog(player_id=player_id, season=season, proxy=proxy, timeout=3).get_data_frames()[0]
                    no_res = False
                    print(player_id, season, proxy)
                    break
                except:
                    # if that fails, move on to next proxy unless out of proxies
                    if (proxy_index + 1) >= len(proxies):
                        # unless tried proxies 5 times
                        if proxy_collection_counter < 6:
                            # if out of proxies: get more proxies, fix counters, and try without a proxy again
                            proxy_index = 0
                            proxy_collection_counter = proxy_collection_counter + 1
                            print(player_id, ' failed {} times'.format(proxy_collection_counter))
                            proxies = get_proxies()
                            break
                        else:
                            return None
                    else:
                        proxy_index = proxy_index + 1

    return res



if __name__ == '__main__':
    # argparse
    description = 'Updates nba database'
    parser = argparse.ArgumentParser(description)
    parser.add_argument('-p','--player', help='Updates players', action='store_true')
    parser.add_argument('-pa', '--player_attributes', help='Updates player attributes', action='store_true')
    parser.add_argument('-hg', '--historical_gamelogs', help='Updates historical player gamelogs', action='store_true')
    parser.add_argument('-cg', '--current_gamelogs', help='Updates current player gamelogs', action='store_true')
    args = parser.parse_args()

    conn = sql.connect('data/nba.sqlite')

    # get proxies
    proxies = get_proxies()

    # define seasons
    SEASONS_HISTORICAL = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    SEASON_CURRENT = [2021]

    # update players
    if args.player:
        print('Updating players...')
        df_players = update_players(conn)
 
    # update player attributes
    if args.player_attributes:
        print('Updating player attributes...')
        update_player_attributes(conn, proxies)

    # update historical gamelogs
    if args.historical_gamelogs:
        print('Updating historical player gamelogs...')
        update_gamelogs(conn, proxies, SEASONS_HISTORICAL, hist=True)
    
    # update current gamelogs
    if args.current_gamelogs:
        print('Updating current gamelogs...')
        update_gamelogs(conn, proxies, SEASON_CURRENT, hist=False)


