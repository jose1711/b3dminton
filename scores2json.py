#!/usr/bin/env python
"""
reads data on console and append them to bedminton-game-data.json
where it's read by stats-making script
"""
import pandas as pd
import json
import re
import sys
import time
from subprocess import getoutput as _go

player_names = []
date = ''
score_args = []

player2alias = {
    'žaneta': 'zanet',
    'tomáš': 'tomas',
}


def alias(player):
    if player in player2alias:
        return player2alias[player]
    else:
        return player


player_names = _go('''curl -s https://freeshell.de/~jose1711/bedas_slavia2.pdf | \
                 pdftotext - - | sort -u | grep -e '[a-z]' ''')

player_names = [x.lower() for x in player_names.splitlines()]

detected_date = [x for x in player_names if 'badminton' in x][0]
pattern = re.compile(r'.* (?P<year>20[0-9]{2}) \((?P<day>..)\.(?P<month>..)\.\)')
match = pattern.match(detected_date)
day, month, year = [match.group(x) for x in ('day', 'month', 'year')]

detected_date = '{}{}{}'.format(year, month, day)
detected_player_names = [x for x in player_names if 'badminton' not in x]
player_names = []

if len(sys.argv) > 1:
    print('You provided game data on input, so let\'s use that')
    date = time.strftime("%Y%m%d")
    player_names = ['agi', 'jose', 'janko']
    score_args = iter(sys.argv[1:])

if not date:
    date = input('Date ([{}]): '.format(detected_date))

if not date:
    date = detected_date

if not re.match('20[0-9]{2}[01][0-9]{3}$', date):
    raise Exception('Date format not recognized')

if not player_names:
    player_names = sorted(input('Player names ('
                                '[{}]): '.format(detected_player_names)).split())

if not player_names:
    player_names = detected_player_names

player_names = list(map(alias, player_names))

if len(player_names) < 2:
    raise Exception('At least 2 players required!')

index = pd.MultiIndex.from_tuples([(pd.to_datetime(date), x)
                                   for x in player_names])

print('Sorted player names: {}'.format(player_names))

total = len(player_names) * (len(player_names) - 1)
total /= 2
total = int(total)
counter = 0

df = pd.DataFrame(index=index, columns=player_names)
for column_ix in range(0, len(player_names)):
    for row_ix in range(column_ix, len(player_names)):
        if column_ix == row_ix:
            continue
        counter += 1
        first = player_names[column_ix]
        second = player_names[row_ix]
        while True:
            try:
                score = int(score_args.__next__())
                break
            except:
                pass

            try:
                score = input('({0}/{1}) {2} vs {3}: '.format(counter,
                                                              total,
                                                              first,
                                                              second))
                if not score:
                    score = 0
                score = int(score)
                break
            except ValueError:
                print('Invalid input: {}'.format(score))
                pass

        if score == 0:
            print('No match data, skipping')
            continue
        # we won, they lost
        if score > 0:
            their_score = score * -1
            if abs(their_score) > 13:
                my_score = abs(their_score) + 2
            else:
                my_score = 15
        # we lost, they won
        else:
            my_score = score
            if abs(my_score) > 13:
                their_score = abs(my_score) + 2
            else:
                their_score = 15
        print('{0}  {1}'.format(first, second))
        print('{0}  {1}'.format(my_score, their_score))
        df[first][row_ix] = my_score
        df[second][column_ix] = their_score
        print(df)

jsondata = json.dumps([date, player_names, df.fillna(0).values.tolist()])
with open('bedminton-game-data.json', 'a') as f:
    f.write(jsondata + '\n')
