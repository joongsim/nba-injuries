import csv
import requests

from bs4 import BeautifulSoup
from dateutil.parser import parse
from string import ascii_lowercase

def scrape_refs(letter='a'):
    '''
    Gathers name, start year, end year, position, height, weight, birth date, and college
    of players whose last names begin with a certain letter
    
    Keyword arguments:
    letter - first letter of last names

    Returns:
    list of dicts with key = player name, value = dictionary of start year, end year,
        position, height, weight, birthdate, and college
    '''
    URL = 'https://www.basketball-reference.com/players/' + letter +'/'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Scrapes every entry under name column from table body
    raw_names = soup.tbody.find_all('th')
    raw_names_list = []
    for name in raw_names:
        raw_names_list.append(name.a.string)

    # Scrapes every entry for all other columns from table body
    raw_stats = soup.tbody.find_all(['td'])
    raw_stats_list = []
    for line in raw_stats:
        raw_stats_list.append(line.string)

    l = []

    z = zip(raw_names_list, 
        raw_stats_list[::7], 
        raw_stats_list[1::7], 
        raw_stats_list[2::7], 
        raw_stats_list[3::7], 
        raw_stats_list[4::7], 
        raw_stats_list[5::7], 
        raw_stats_list[6::7])

    for name, from_, to_, pos, ht, wt, bday, coll in z:
        d = {}

        d['Name'] = name
        d['From'] = from_
        d['Position'] = pos
        d['Height'] = ht
        d['Weight'] = wt
        d['To'] = to_
        
        # Parse birth date using dateutil.parser.parse()
        if bday is not None:
            d['Birth Date'] = parse(bday).date()

        d['College'] = coll

        l.append(d)

    return l

def write_to_csv(lst=[], filename='bbref_stats.csv'):
    '''
    Writes list of dicts to csv file
    '''
    fields = lst[0].keys()
    with open(filename, 'w') as csvFile:
        dict_writer = csv.DictWriter(csvFile, fields)
        dict_writer.writeheader()
        dict_writer.writerows(lst)








if __name__ == '__main__':
    for char in ascii_lowercase:  
        fout = 'data/bbref_' + char + '.csv'
        print(fout)
        print(char)
        l = scrape_refs(char)
        if l:
            write_to_csv(l, fout)