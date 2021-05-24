import nba_api.stats.static.players as players
from nba_api.stats import endpoints


# Gets player bio/stats for season
# Returns dataframe
def _get_bios(season='current_season'):
    return endpoints.LeagueDashPlayerBioStats().get_data_frames()[0]

    
# build dict of bio dataframes over multiple seasons
def build_bios_dict(seasons=[]):
    bios_dict = {}
    for season in seasons:
        df = _get_bios(season)
        bios_dict[season] = df
    return bios_dict


# Write dfs to csv
def bios_to_csv(bios_dict):
    for season in bios_dict:
        filename = 'bios' + season + '.csv'
        bios_dict[season].to_csv('data/' + filename, index=False)
        

if __name__ == '__main__':
    SEASONS = ['2012-13', '2013-14', '2014-15', '2015-16', '2016-17', '2017-18', '2018-19']
    
    bios_dict = build_bios_dict(SEASONS)
    bios_to_csv(bios_dict)