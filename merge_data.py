import pandas as pd

from fuzzywuzzy import process
from nba_api.stats.static.players import get_players

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
    bref_df = pd.read_csv('data/bbref_stats.csv')
    inj_df = pd.read_csv('data/injuries.csv')
    players_df = pd.DataFrame(get_players())

    
    mult_names = inj_df[inj_df['Player'].str.contains('/')]
    one_name = inj_df[~inj_df['Player'].str.contains('/')]
    # converting full_name series to dict for performance
    player_names_dict = players_df['full_name'].to_dict()

    