import argparse
import csv
from os import write
import requests


from bs4 import BeautifulSoup
from dateutil.parser import parse
from string import ascii_lowercase

def scrape_refs(letters=ascii_lowercase):
    '''
    Gathers name, start year, end year, position, height, weight, birth date, and college
    of players whose last names begin with a certain letter
    
    Arguments:
    letter - character or string representing first letter(s) of last name. 
                Default value is all letters a-z.

    Returns:
    list of dicts with player name, start year, end year,
        position, height, weight, birthdate, and college
    '''

    # Initialize lists
    raw_names_list = []
    raw_stats_list = []
    final_list = []
    iteration = 1

    for char in letters:
        print('Progress: ' + str(iteration*100//len(letters)) + '%', end='\r')

        URL = 'https://www.basketball-reference.com/players/' + char +'/'
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Scrapes every entry under name column from table body
        raw_names = soup.tbody.find_all('th')
        
        for name in raw_names:
            raw_names_list.append(name.a.string)

        # Scrapes every entry for all other columns from table body
        raw_stats = soup.tbody.find_all(['td'])
        for line in raw_stats:
            raw_stats_list.append(line.string)

        iteration += 1

    print('Scraping complete...')

    # Zip fields and store as dictionary
    z = zip(raw_names_list, 
        raw_stats_list[::7], 
        raw_stats_list[1::7], 
        raw_stats_list[2::7], 
        raw_stats_list[3::7], 
        raw_stats_list[4::7], 
        raw_stats_list[5::7], 
        raw_stats_list[6::7])


    print('Compiling results...')
    for name, from_, to_, pos, ht, wt, bday, coll in z:
        d = {}

        d['Name'] = name
        d['From'] = from_
        d['To'] = to_
        d['Position'] = pos
        d['Height'] = ht
        d['Weight'] = wt
        
        # Parse birth date using dateutil.parser.parse()
        if bday is not None:
            d['Birth Date'] = parse(bday).date()

        d['College'] = coll

        final_list.append(d)

    return final_list

def write_to_csv(lst=[], filename='bbref_stats.csv'):
    '''
    Writes list of dicts to csv file
    '''
    print('Writing to: ' + filename)
    fields = lst[0].keys()
    with open(filename, 'w') as csvFile:
        dict_writer = csv.DictWriter(csvFile, fields)
        dict_writer.writeheader()
        dict_writer.writerows(lst)








if __name__ == '__main__':
    
    # Argument parser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--letters', type=str, default=ascii_lowercase)
    parser.add_argument('--path', type=str, default='bbref_stats.csv')
    args = parser.parse_args()

    print('Scraping players with last initial in: ' + args.letters.upper())

    l = scrape_refs(args.letters)
    write_to_csv(l, args.path)

    print('Done!')