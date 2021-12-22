import pandas as pd

from nba_api.stats.endpoints import CommonPlayerInfo
from nba_api.stats.static.players import get_players
from time import sleep

def get_common_player_info():
    all_players = get_players()
    id_list = [player['id'] for player in all_players]

    info_list = []
    for index, id in enumerate(id_list):
        print('Fetching player {} of {}'.format(index + 1, len(id_list)), end='\r')
        info_list.append(CommonPlayerInfo(player_id=id).get_normalized_dict()['CommonPlayerInfo'][0])
        sleep(3)

    return pd.DataFrame(info_list)

    


if __name__ == '__main__':
    path = 'data/player_info.csv'

    df = get_common_player_info()
    df.to_csv(path, index=False)
    
